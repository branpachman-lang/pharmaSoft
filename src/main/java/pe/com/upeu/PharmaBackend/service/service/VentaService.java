package pe.com.upeu.PharmaBackend.service.service;
import pe.com.upeu.PharmaBackend.dto.VentaRequestDTO;
import pe.com.upeu.PharmaBackend.dto.VentaResponseDTO;

import java.util.List;

public interface VentaService {
    VentaResponseDTO registrar(VentaRequestDTO request);
    VentaResponseDTO buscar(Long id);
    List<VentaResponseDTO> listar();
}