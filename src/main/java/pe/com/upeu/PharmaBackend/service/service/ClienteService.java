package pe.com.upeu.PharmaBackend.service.service;
import pe.com.upeu.PharmaBackend.dto.ClienteRequestDTO;
import pe.com.upeu.PharmaBackend.dto.ClienteResponseDTO;
import pe.com.upeu.PharmaBackend.service.generic.CrudService;

public interface ClienteService extends CrudService<ClienteRequestDTO, ClienteResponseDTO, Long> {
}