package pe.com.upeu.PharmaBackend.security;

import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.web.filter.OncePerRequestFilter;
import java.io.IOException;
/*
 * Se ejecuta una vez por peticion, antes de la autorizacion.
 *
 * 1. Lee el encabezado Authorization: Bearer <token>.
 * 2. Valida firma y expiracion del token.
 * 3. Carga el usuario y, si esta habilitado, lo deja autenticado en el
 * SecurityContext para el resto de la peticion.
 *
 * Si no hay token o es invalido, NO corta la peticion: la deja seguir
 * sin autenticar. Si el endpoint es protegido, Spring Security llamara
 * al AuthenticationEntryPoint, que responde 401 con el motivo guardado
 * en el atributo ATRIBUTO_ERROR.
 *
 * No se registra como @Component: lo crea SecurityConfig para que solo
 * actue dentro de la cadena de seguridad.
 */
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    public static final String ATRIBUTO_ERROR = "jwt.error";
    private static final Logger log =
            LoggerFactory.getLogger(JwtAuthenticationFilter.class);
    private static final String PREFIJO = "Bearer ";
    private final JwtService jwtService;
    private final UserDetailsService userDetailsService;
    public JwtAuthenticationFilter(
            JwtService jwtService,
            UserDetailsService userDetailsService) {
        this.jwtService = jwtService;
        this.userDetailsService = userDetailsService;
    }
    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
                    HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {
        String encabezado = request.getHeader(HttpHeaders.AUTHORIZATION);
        if (encabezado == null || !encabezado.startsWith(PREFIJO)) {
            filterChain.doFilter(request, response);
            return;
        }
        String token = encabezado.substring(PREFIJO.length()).trim();
        try {
            String username = jwtService.extraerUsername(token);
            if (username != null
                    && SecurityContextHolder.getContext().getAuthentication() == null) {
// Se consulta la base en cada peticion: si el usuario fue
// deshabilitado despues de emitir el token, deja de entrar.
                UserDetails usuario = userDetailsService.loadUserByUsername(username);
                if (usuario.isEnabled()) {
                    UsernamePasswordAuthenticationToken autenticacion =
                            new UsernamePasswordAuthenticationToken(
                                    usuario, null, usuario.getAuthorities());
                    autenticacion.setDetails(
                            new WebAuthenticationDetailsSource().buildDetails(request));
                    SecurityContextHolder.getContext().setAuthentication(autenticacion);
                } else {
                    request.setAttribute(ATRIBUTO_ERROR, "El usuario está deshabilitado");
                }
            }
        } catch (ExpiredJwtException ex) {
            log.debug("Token expirado en {}", request.getRequestURI());
            request.setAttribute(ATRIBUTO_ERROR,
                    "El token ha expirado. Inicie sesión nuevamente");
        } catch (UsernameNotFoundException ex) {
            log.warn("Token de un usuario que ya no existe en {}", request.getRequestURI());
            request.setAttribute(ATRIBUTO_ERROR, "El usuario del token no existe");
        } catch (JwtException | IllegalArgumentException ex) {
            log.warn("Token inválido en {}: {}", request.getRequestURI(), ex.getMessage());
            request.setAttribute(ATRIBUTO_ERROR, "El token no es válido");
        }
        filterChain.doFilter(request, response);
    }
}