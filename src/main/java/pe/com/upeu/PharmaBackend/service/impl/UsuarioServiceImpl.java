package pe.com.upeu.PharmaBackend.service.impl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Sort;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pe.com.upeu.PharmaBackend.dto.auth.EmpleadoResponseDTO;
import pe.com.upeu.PharmaBackend.dto.auth.RolResponseDTO;
import pe.com.upeu.PharmaBackend.dto.auth.UsuarioRequestDTO;
import pe.com.upeu.PharmaBackend.dto.auth.UsuarioResponseDTO;
import pe.com.upeu.PharmaBackend.entity.Empleado;
import pe.com.upeu.PharmaBackend.entity.Rol;
import pe.com.upeu.PharmaBackend.entity.Usuario;
import pe.com.upeu.PharmaBackend.exception.RecursoNoEncontradoException;
import pe.com.upeu.PharmaBackend.exception.ReglaNegocioException;
import pe.com.upeu.PharmaBackend.mapper.UsuarioMapper;
import pe.com.upeu.PharmaBackend.repository.EmpleadoRepository;
import pe.com.upeu.PharmaBackend.repository.RolRepository;
import pe.com.upeu.PharmaBackend.repository.UsuarioRepository;
import pe.com.upeu.PharmaBackend.service.service.UsuarioService;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.stream.Collectors;
@Service
public class UsuarioServiceImpl implements UsuarioService {
    private static final Logger log =
            LoggerFactory.getLogger(UsuarioServiceImpl.class);
    private final UsuarioRepository usuarioRepository;
    private final EmpleadoRepository empleadoRepository;
    private final RolRepository rolRepository;
    private final PasswordEncoder passwordEncoder;
    private final UsuarioMapper usuarioMapper;
    public UsuarioServiceImpl(
            UsuarioRepository usuarioRepository,
            EmpleadoRepository empleadoRepository,
            RolRepository rolRepository,
            PasswordEncoder passwordEncoder,
            UsuarioMapper usuarioMapper) {
        this.usuarioRepository = usuarioRepository;
        this.empleadoRepository = empleadoRepository;
        this.rolRepository = rolRepository;
        this.passwordEncoder = passwordEncoder;
        this.usuarioMapper = usuarioMapper;
    }
    /*
     * Crea la cuenta de un empleado y le asigna uno o varios roles.
     *
     * Reglas:
     * - el empleado existe (404) y esta activo (409);
     * - el empleado aun no tiene usuario (409): relacion 1 a 1;
     * - todos los roles existen (404): relacion muchos a muchos;
     * - el username no se repite (409).
     */
    @Override
    @Transactional
    public UsuarioResponseDTO crear(UsuarioRequestDTO request) {
        String username = request.getUsername().trim().toLowerCase(Locale.ROOT);
        log.info("Registrando usuario={} empleadoId={} rolIds={}",
                username, request.getEmpleadoId(), request.getRolIds());
        Empleado empleado = empleadoRepository.findById(request.getEmpleadoId())
                .orElseThrow(() -> new RecursoNoEncontradoException(
                        "Empleado no encontrado con id: " + request.getEmpleadoId()));
        if (!Boolean.TRUE.equals(empleado.getEstado())) {
            throw new ReglaNegocioException(
                    "El empleado " + empleado.getNombreCompleto() + " está inactivo");
        }
        if (usuarioRepository.existsByEmpleadoId(empleado.getId())) {
            throw new ReglaNegocioException(
                    "El empleado " + empleado.getNombreCompleto() + " ya tiene un usuario");
        }
        if (usuarioRepository.existsByUsernameIgnoreCase(username)) {
            throw new ReglaNegocioException(
                    "Ya existe un usuario con el nombre: " + username);
        }
        List<Rol> roles = rolRepository.findAllById(request.getRolIds());
        if (roles.size() != request.getRolIds().size()) {
            Set<Long> encontrados = roles.stream().map(Rol::getId).collect(Collectors.toSet());
            Set<Long> faltantes = new HashSet<>(request.getRolIds());
            faltantes.removeAll(encontrados);
            throw new RecursoNoEncontradoException("Roles no encontrados: " + faltantes);
        }
// BCrypt solo admite 72 BYTES: una ñ o una tilde ocupan 2 bytes en UTF-8
        if (request.getPassword().getBytes(StandardCharsets.UTF_8).length > 72) {
            throw new ReglaNegocioException("La contraseña no puede superar 72 bytes");
        }
        Usuario usuario = new Usuario();
        usuario.setUsername(username);
// Se guarda el hash BCrypt, nunca la contrasena en texto plano
        usuario.setPassword(passwordEncoder.encode(request.getPassword()));
        usuario.setEstado(true);
        usuario.setEmpleado(empleado);
        usuario.setRoles(new HashSet<>(roles));
        Usuario guardado = usuarioRepository.save(usuario);
        log.info("Usuario registrado id={} usuario={} roles={}",
                guardado.getId(), username, usuarioMapper.nombresRoles(roles));
        return usuarioMapper.toUsuarioResponse(guardado);
    }
    @Override
    @Transactional(readOnly = true)
    public List<UsuarioResponseDTO> listar() {
        return usuarioRepository.findAll(Sort.by("username"))
                .stream()
                .map(usuarioMapper::toUsuarioResponse)
                .toList();
    }
    @Override
    @Transactional(readOnly = true)
    public List<EmpleadoResponseDTO> listarEmpleados() {
        Set<Long> conUsuario = usuarioRepository.findEmpleadoIdsConUsuario();
        return empleadoRepository.findAll(Sort.by("apellidos", "nombres"))
                .stream()
                .map(e -> usuarioMapper.toEmpleadoResponse(e, conUsuario.contains(e.getId())))
                .toList();
    }
    @Override
    @Transactional(readOnly = true)
    public List<RolResponseDTO> listarRoles() {
        return rolRepository.findAll(Sort.by("nombre"))
                .stream()
                .map(usuarioMapper::toRolResponse)
                .toList();
    }
}