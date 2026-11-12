package pe.com.upeu.PharmaBackend.service.impl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pe.com.upeu.PharmaBackend.auditoria.AuditoriaListener;
import pe.com.upeu.PharmaBackend.auditoria.EventoAuditoria;
import pe.com.upeu.PharmaBackend.dto.auth.LoginRequestDTO;
import pe.com.upeu.PharmaBackend.dto.auth.LoginResponseDTO;
import pe.com.upeu.PharmaBackend.dto.auth.UsuarioResponseDTO;
import pe.com.upeu.PharmaBackend.dto.auth.CambioPasswordRequestDTO;
import pe.com.upeu.PharmaBackend.entity.Usuario;
import pe.com.upeu.PharmaBackend.exception.RecursoNoEncontradoException;
import pe.com.upeu.PharmaBackend.exception.ReglaNegocioException;
import pe.com.upeu.PharmaBackend.mapper.UsuarioMapper;
import pe.com.upeu.PharmaBackend.repository.UsuarioRepository;
import pe.com.upeu.PharmaBackend.security.JwtService;
import pe.com.upeu.PharmaBackend.security.PermisosPorRol;
import pe.com.upeu.PharmaBackend.service.service.AuthService;
import org.springframework.security.crypto.password.PasswordEncoder;
import java.nio.charset.StandardCharsets;
import java.util.List;
@Service
public class AuthServiceImpl implements AuthService {
    private static final Logger log =
            LoggerFactory.getLogger(AuthServiceImpl.class);
    private final AuthenticationManager authenticationManager;
    private final JwtService jwtService;
    private final UsuarioRepository usuarioRepository;
    private final UsuarioMapper usuarioMapper;
    private final PasswordEncoder passwordEncoder;
    private final AuditoriaListener auditoria;
    public AuthServiceImpl(
            AuthenticationManager authenticationManager,
            JwtService jwtService,
            UsuarioRepository usuarioRepository,
            UsuarioMapper usuarioMapper,
            PasswordEncoder passwordEncoder, AuditoriaListener auditoria) {
        this.authenticationManager = authenticationManager;
        this.jwtService = jwtService;
        this.usuarioRepository = usuarioRepository;
        this.usuarioMapper = usuarioMapper;
        this.passwordEncoder = passwordEncoder;
        this.auditoria = auditoria;
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
        Authentication autenticacion;
        try {
            autenticacion = authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(username, request.getPassword()));
        } catch (AuthenticationException ex) {
            auditoria.registrar(EventoAuditoria.login("LOGIN_FALLIDO", username));
            throw ex;
        }
        UserDetails principal = (UserDetails) autenticacion.getPrincipal();
        Usuario usuario = buscar(principal.getUsername());
        String token = jwtService.generarToken(principal);
        List<String> roles = usuarioMapper.nombresRoles(usuario.getRoles());
        auditoria.registrar(EventoAuditoria.login("LOGIN_EXITOSO", usuario.getUsername()));
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

    @Override
    @Transactional
    public void cambiarPassword(String username, CambioPasswordRequestDTO request) {
        Usuario usuario = buscar(username);
        if (!passwordEncoder.matches(request.getPasswordActual(), usuario.getPassword())) {
            throw new ReglaNegocioException("La contraseña actual no es correcta");
        }
        if (passwordEncoder.matches(request.getPasswordNueva(), usuario.getPassword())) {
            throw new ReglaNegocioException("La nueva contraseña debe ser distinta de la actual");
        }
        if (request.getPasswordNueva().getBytes(StandardCharsets.UTF_8).length > 72) {
            throw new ReglaNegocioException("La contraseña no puede superar 72 bytes");
        }
        usuario.setPassword(passwordEncoder.encode(request.getPasswordNueva()));
        usuarioRepository.save(usuario);
        log.info("Contraseña actualizada para usuario={}", usuario.getUsername());
    }
    private Usuario buscar(String username) {
        return usuarioRepository.findByUsernameIgnoreCase(username)
                .orElseThrow(() -> new RecursoNoEncontradoException(
                        "Usuario no encontrado: " + username));
    }
}
