package pe.com.upeu.PharmaBackend.service.service;

import pe.com.upeu.PharmaBackend.dto.CategoriaRequestDTO;
import pe.com.upeu.PharmaBackend.dto.CategoriaResponseDTO;
import pe.com.upeu.PharmaBackend.service.generic.CrudService;
import pe.com.upeu.PharmaBackend.dto.PaginaResponseDTO;

public interface CategoriaService extends CrudService<CategoriaRequestDTO, CategoriaResponseDTO, Long> {
    PaginaResponseDTO<CategoriaResponseDTO> listarPaginado(int pagina, int tamanio, String ordenarPor, String direccion);
}
