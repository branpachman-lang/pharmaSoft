package pe.com.upeu.PharmaBackend.service.impl;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.crypto.password.PasswordEncoder;
import pe.com.upeu.PharmaBackend.dto.auth.AsignarRolesRequestDTO;
import pe.com.upeu.PharmaBackend.dto.auth.CambioPasswordRequestDTO;
import pe.com.upeu.PharmaBackend.dto.auth.EstadoUsuarioRequestDTO;
import pe.com.upeu.PharmaBackend.entity.Rol;
import pe.com.upeu.PharmaBackend.entity.Usuario;
import pe.com.upeu.PharmaBackend.exception.RecursoNoEncontradoException;
import pe.com.upeu.PharmaBackend.exception.ReglaNegocioException;
import pe.com.upeu.PharmaBackend.mapper.UsuarioMapper;
import pe.com.upeu.PharmaBackend.repository.EmpleadoRepository;
import pe.com.upeu.PharmaBackend.repository.RolRepository;
import pe.com.upeu.PharmaBackend.repository.UsuarioRepository;
import pe.com.upeu.PharmaBackend.security.JwtService;

import java.util.List;
import java.util.Optional;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class SeguridadAutonomaServiceTest {
    @Mock AuthenticationManager authenticationManager;
    @Mock JwtService jwtService;
    @Mock UsuarioRepository usuarioRepository;
    @Mock EmpleadoRepository empleadoRepository;
    @Mock RolRepository rolRepository;
    @Mock UsuarioMapper usuarioMapper;
    @Mock PasswordEncoder passwordEncoder;
    @InjectMocks AuthServiceImpl authService;
    @InjectMocks UsuarioServiceImpl usuarioService;

    private Usuario cuenta(String nombre) {
        Usuario usuario = new Usuario();
        usuario.setId(7L);
        usuario.setUsername(nombre);
        usuario.setPassword("hashAnterior");
        usuario.setEstado(true);
        return usuario;
    }

    private CambioPasswordRequestDTO cambio(String actual, String nueva) {
        CambioPasswordRequestDTO dto = new CambioPasswordRequestDTO();
        dto.setPasswordActual(actual);
        dto.setPasswordNueva(nueva);
        return dto;
    }

    @Test
    void cambioPasswordSoloActualizaLaCuentaAutenticadaYGuardaHash() {
        Usuario usuario = cuenta("vendedor");
        when(usuarioRepository.findByUsernameIgnoreCase("vendedor")).thenReturn(Optional.of(usuario));
        when(passwordEncoder.matches("Anterior2026", "hashAnterior")).thenReturn(true);
        when(passwordEncoder.encode("NuevaClave2026")).thenReturn("hashNuevo");

        authService.cambiarPassword("vendedor", cambio("Anterior2026", "NuevaClave2026"));

        assertEquals("hashNuevo", usuario.getPassword());
        verify(usuarioRepository).save(usuario);
        verify(passwordEncoder).encode("NuevaClave2026");
    }

    @Test
    void rechazaPasswordActualIncorrectaSinModificarHash() {
        Usuario usuario = cuenta("vendedor");
        when(usuarioRepository.findByUsernameIgnoreCase("vendedor")).thenReturn(Optional.of(usuario));
        assertEquals("La contraseña actual no es correcta",
                assertThrows(ReglaNegocioException.class,
                        () -> authService.cambiarPassword("vendedor", cambio("Mala2026", "NuevaClave2026")))
                        .getMessage());
        assertEquals("hashAnterior", usuario.getPassword());
        verify(usuarioRepository, never()).save(any());
    }

    @Test
    void rechazaPasswordNuevaIgualALaActual() {
        Usuario usuario = cuenta("vendedor");
        when(usuarioRepository.findByUsernameIgnoreCase("vendedor")).thenReturn(Optional.of(usuario));
        when(passwordEncoder.matches("Anterior2026", "hashAnterior")).thenReturn(true);
        assertEquals("La nueva contraseña debe ser distinta de la actual",
                assertThrows(ReglaNegocioException.class,
                        () -> authService.cambiarPassword("vendedor", cambio("Anterior2026", "Anterior2026")))
                        .getMessage());
        verify(usuarioRepository, never()).save(any());
    }

    @Test
    void asignarRolesReemplazaElConjuntoExistente() {
        Usuario usuario = cuenta("vendedor");
        usuario.setRoles(Set.of(new Rol(2L, "VENDEDOR", null)));
        AsignarRolesRequestDTO dto = new AsignarRolesRequestDTO();
        dto.setRolIds(Set.of(2L, 3L));
        when(usuarioRepository.findById(7L)).thenReturn(Optional.of(usuario));
        when(rolRepository.findAllById(dto.getRolIds())).thenReturn(List.of(
                new Rol(2L, "VENDEDOR", null), new Rol(3L, "ALMACENERO", null)));
        when(usuarioRepository.save(usuario)).thenReturn(usuario);

        usuarioService.asignarRoles(7L, dto, "admin");

        assertEquals(Set.of("VENDEDOR", "ALMACENERO"),
                usuario.getRoles().stream().map(Rol::getNombre).collect(java.util.stream.Collectors.toSet()));
        verify(usuarioRepository).save(usuario);
    }

    @Test
    void adminNoPuedeQuitarseSuRol() {
        Usuario usuario = cuenta("admin");
        usuario.setRoles(Set.of(new Rol(1L, "ADMIN", null)));
        AsignarRolesRequestDTO dto = new AsignarRolesRequestDTO();
        dto.setRolIds(Set.of(2L));
        when(usuarioRepository.findById(7L)).thenReturn(Optional.of(usuario));
        when(rolRepository.findAllById(dto.getRolIds())).thenReturn(List.of(new Rol(2L, "VENDEDOR", null)));

        assertThrows(ReglaNegocioException.class,
                () -> usuarioService.asignarRoles(7L, dto, "admin"));
        verify(usuarioRepository, never()).save(any());
    }

    @Test
    void rolInexistenteProduce404() {
        Usuario usuario = cuenta("vendedor");
        AsignarRolesRequestDTO dto = new AsignarRolesRequestDTO();
        dto.setRolIds(Set.of(999L));
        when(usuarioRepository.findById(7L)).thenReturn(Optional.of(usuario));
        when(rolRepository.findAllById(dto.getRolIds())).thenReturn(List.of());

        assertThrows(RecursoNoEncontradoException.class,
                () -> usuarioService.asignarRoles(7L, dto, "admin"));
        verify(usuarioRepository, never()).save(any());
    }

    @Test
    void desactivarUsuarioConservaLaCuenta() {
        Usuario usuario = cuenta("vendedor");
        EstadoUsuarioRequestDTO dto = new EstadoUsuarioRequestDTO();
        dto.setEstado(false);
        when(usuarioRepository.findById(7L)).thenReturn(Optional.of(usuario));
        when(usuarioRepository.save(usuario)).thenReturn(usuario);

        usuarioService.cambiarEstado(7L, dto, "admin");

        assertFalse(usuario.getEstado());
        verify(usuarioRepository).save(usuario);
        verify(usuarioRepository, never()).delete(any());
    }

    @Test
    void adminNoPuedeDesactivarse() {
        Usuario usuario = cuenta("admin");
        EstadoUsuarioRequestDTO dto = new EstadoUsuarioRequestDTO();
        dto.setEstado(false);
        when(usuarioRepository.findById(7L)).thenReturn(Optional.of(usuario));

        assertThrows(ReglaNegocioException.class,
                () -> usuarioService.cambiarEstado(7L, dto, "admin"));
        assertTrue(usuario.getEstado());
        verify(usuarioRepository, never()).save(any());
    }
}
