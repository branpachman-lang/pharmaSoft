package pe.com.upeu.PharmaBackend.service.service;
import pe.com.upeu.PharmaBackend.dto.auth.LoginRequestDTO;
import pe.com.upeu.PharmaBackend.dto.auth.LoginResponseDTO;
import pe.com.upeu.PharmaBackend.dto.auth.UsuarioResponseDTO;
public interface AuthService {
    LoginResponseDTO login(LoginRequestDTO request);
    UsuarioResponseDTO usuarioActual(String username);
}