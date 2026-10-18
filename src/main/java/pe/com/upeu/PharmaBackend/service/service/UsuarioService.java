package pe.com.upeu.PharmaBackend.service.service;
import pe.com.upeu.PharmaBackend.dto.auth.EmpleadoResponseDTO;
import pe.com.upeu.PharmaBackend.dto.auth.RolResponseDTO;
import pe.com.upeu.PharmaBackend.dto.auth.UsuarioRequestDTO;
import pe.com.upeu.PharmaBackend.dto.auth.UsuarioResponseDTO;
import pe.com.upeu.PharmaBackend.dto.auth.AsignarRolesRequestDTO;
import pe.com.upeu.PharmaBackend.dto.auth.EstadoUsuarioRequestDTO;
import java.util.List;
public interface UsuarioService {
    UsuarioResponseDTO crear(UsuarioRequestDTO request);
    List<UsuarioResponseDTO> listar();
    List<EmpleadoResponseDTO> listarEmpleados();
    List<RolResponseDTO> listarRoles();
    UsuarioResponseDTO asignarRoles(Long id, AsignarRolesRequestDTO request, String actor);
    UsuarioResponseDTO cambiarEstado(Long id, EstadoUsuarioRequestDTO request, String actor);
}
