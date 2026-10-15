package pe.com.upeu.PharmaBackend.service.impl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pe.com.upeu.PharmaBackend.dto.auth.LoginRequestDTO;
import pe.com.upeu.PharmaBackend.dto.auth.LoginResponseDTO;
import pe.com.upeu.PharmaBackend.dto.auth.UsuarioResponseDTO;
import pe.com.upeu.PharmaBackend.entity.Usuario;
import pe.com.upeu.PharmaBackend.exception.RecursoNoEncontradoException;
import pe.com.upeu.PharmaBackend.mapper.UsuarioMapper;
import pe.com.upeu.PharmaBackend.repository.UsuarioRepository;
import pe.com.upeu.PharmaBackend.security.JwtService;
import pe.com.upeu.PharmaBackend.security.PermisosPorRol;
import pe.com.upeu.PharmaBackend.service.service.AuthService;
import java.util.List;
@Service
public class AuthServiceImpl implements AuthService {
    private static final Logger log =
            LoggerFactory.getLogger(AuthServiceImpl.class);
    private final AuthenticationManager authenticationManager;
    private final JwtService jwtService;
    private final UsuarioRepository usuarioRepository;
    private final UsuarioMapper usuarioMapper;
    public AuthServiceImpl(
            AuthenticationManager authenticationManager,
            JwtService jwtService,
            UsuarioRepository usuarioRepository,
                    UsuarioMapper usuarioMapper) {
        this.authenticationManager = authenticationManager;
        this.jwtService = jwtService;
        this.usuarioRepository = usuarioRepository;
        this.usuarioMapper = usuarioMapper;
    }
    /*
     * 1. AuthenticationManager busca al usuario (UsuarioDetailsService),
     * verifica que este habilitado y compara la contrasena con el hash
     * usando BCrypt. Si algo falla lanza una AuthenticationException,
     * que GlobalExceptionHandler convierte en 401.
     * 2. Si todo es correcto, se emite el JWT.
     *
     * La contrasena NUNCA se escribe en el log.
     */
    @Override
    @Transactional(readOnly = true)
    public LoginResponseDTO login(LoginRequestDTO request) {
        String username = request.getUsername().trim();
        log.info("Intento de inicio de sesión: usuario={}", username);
        Authentication autenticacion = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(username, request.getPassword()));
        UserDetails principal = (UserDetails) autenticacion.getPrincipal();
        Usuario usuario = buscar(principal.getUsername());
        String token = jwtService.generarToken(principal);
        List<String> roles = usuarioMapper.nombresRoles(usuario.getRoles());
        log.info("Inicio de sesión correcto: usuario={} roles={}",
                usuario.getUsername(), roles);
        return new LoginResponseDTO(
                token,
                "Bearer",
                jwtService.getExpiracionSegundos(),
                usuario.getUsername(),
                usuario.getEmpleado().getNombreCompleto(),
                roles,
                PermisosPorRol.permisos(usuario.getRoles())
        );
    }
    @Override
    @Transactional(readOnly = true)
    public UsuarioResponseDTO usuarioActual(String username) {
        return usuarioMapper.toUsuarioResponse(buscar(username));
    }
    private Usuario buscar(String username) {
        return usuarioRepository.findByUsernameIgnoreCase(username)
                .orElseThrow(() -> new RecursoNoEncontradoException(
                        "Usuario no encontrado: " + username));
    }
}