package pe.com.upeu.PharmaBackend.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pe.com.upeu.PharmaBackend.dto.ClienteRequestDTO;
import pe.com.upeu.PharmaBackend.dto.ClienteResponseDTO;
import pe.com.upeu.PharmaBackend.dto.PaginaResponseDTO;
import pe.com.upeu.PharmaBackend.entity.Cliente;
import pe.com.upeu.PharmaBackend.exception.RecursoNoEncontradoException;
import pe.com.upeu.PharmaBackend.exception.ReglaNegocioException;
import pe.com.upeu.PharmaBackend.repository.ClienteRepository;
import pe.com.upeu.PharmaBackend.service.service.ClienteService;

import java.util.List;
import java.util.Set;

@RequiredArgsConstructor
@Service
public class ClienteServiceImpl
        implements ClienteService {

    private static final Logger log =
            LoggerFactory.getLogger(ClienteServiceImpl.class);
    private static final Set<String> CAMPOS_ORDENABLES =
            Set.of("id", "dni", "nombres", "apellidos", "email");
    private final ClienteRepository clienteRepository;

    @Override
    @Transactional
    public ClienteResponseDTO create(ClienteRequestDTO request) {

        log.info(
                "Registrando cliente con DNI={}",
                request.getDni()
        );

        String dni = request.getDni().trim();
        String email = request.getEmail()
                .trim()
                .toLowerCase();

        // Regla de negocio 1
        if (clienteRepository.existsByDni(dni)) {
            throw new ReglaNegocioException(
                    "Ya existe un cliente con el DNI: " + dni
            );
        }

        // Regla de negocio 2
        if (clienteRepository.existsByEmailIgnoreCase(email)) {
            throw new ReglaNegocioException(
                    "Ya existe un cliente con el correo: " + email
            );
        }

        Cliente cliente = new Cliente();

        cliente.setDni(dni);
        cliente.setNombres(
                request.getNombres().trim()
        );
        cliente.setApellidos(
                request.getApellidos().trim()
        );
        cliente.setEmail(email);
        cliente.setTelefono(
                normalizar(request.getTelefono())
        );
        cliente.setDireccion(
                normalizar(request.getDireccion())
        );
        cliente.setEstado(request.getEstado());

        Cliente guardado =
                clienteRepository.save(cliente);

        log.info(
                "Cliente registrado correctamente id={}",
                guardado.getId()
        );

        return convertirResponse(guardado);
    }

    @Override
    @Transactional(readOnly = true)
    public ClienteResponseDTO read(Long id) {

        log.info("Buscando cliente id={}", id);

        Cliente cliente =
                clienteRepository.findById(id)
                        .orElseThrow(() ->
                                new RecursoNoEncontradoException(
                                        "Cliente no encontrado con id: " + id
                                )
                        );

        return convertirResponse(cliente);
    }

    @Override
    @Transactional(readOnly = true)
    public List<ClienteResponseDTO> readAll() {

        log.info("Listando clientes");

        return clienteRepository.findAll()
                .stream()
                .map(this::convertirResponse)
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public PaginaResponseDTO<ClienteResponseDTO> listarPaginado(
            int pagina, int tamanio, String ordenarPor, String direccion) {
        if (pagina < 0 || tamanio < 1) {
            throw new ReglaNegocioException(
                    "La página debe ser mayor o igual a 0 y el tamaño mayor que 0");
        }
        if (!CAMPOS_ORDENABLES.contains(ordenarPor)) {
            throw new ReglaNegocioException(
                    "El campo de ordenamiento '" + ordenarPor
                            + "' no está permitido. Campos válidos: " + CAMPOS_ORDENABLES);
        }
        if (!direccion.equalsIgnoreCase("asc")
                && !direccion.equalsIgnoreCase("desc")) {
            throw new ReglaNegocioException(
                    "La dirección de ordenamiento '" + direccion
                            + "' no está permitida. Valores válidos: asc, desc");
        }

        Sort sort = direccion.equalsIgnoreCase("asc")
                ? Sort.by(ordenarPor).ascending()
                : Sort.by(ordenarPor).descending();
        Page<Cliente> resultado = clienteRepository.findAll(
                PageRequest.of(pagina, tamanio, sort));
        List<ClienteResponseDTO> contenido = resultado.getContent()
                .stream()
                .map(this::convertirResponse)
                .toList();
        return new PaginaResponseDTO<>(
                contenido,
                resultado.getNumber(),
                resultado.getSize(),
                resultado.getTotalElements(),
                resultado.getTotalPages(),
                resultado.isLast());
    }

    @Override
    @Transactional
    public ClienteResponseDTO update(Long id, ClienteRequestDTO request) {

        Cliente cliente = clienteRepository.findById(id).orElseThrow(() ->
                                new RecursoNoEncontradoException(
                                        "Cliente no encontrado con id: " + id
                                )
                        );

        String dni = request.getDni().trim();
        String email = request.getEmail()
                .trim()
                .toLowerCase();

        // DNI de otro cliente
        if (clienteRepository
                .existsByDniAndIdNot(dni, id)) {

            throw new ReglaNegocioException(
                    "Ya existe otro cliente con el DNI: "
                            + dni
            );
        }

        // Email de otro cliente
        if (clienteRepository
                .existsByEmailIgnoreCaseAndIdNot(
                        email,
                        id)) {

            throw new ReglaNegocioException(
                    "Ya existe otro cliente con el correo: "
                            + email
            );
        }

        cliente.setDni(dni);
        cliente.setNombres(
                request.getNombres().trim()
        );
        cliente.setApellidos(
                request.getApellidos().trim()
        );
        cliente.setEmail(email);
        cliente.setTelefono(
                normalizar(request.getTelefono())
        );
        cliente.setDireccion(
                normalizar(request.getDireccion())
        );
        cliente.setEstado(request.getEstado());

        Cliente actualizado =
                clienteRepository.save(cliente);

        log.info(
                "Cliente id={} actualizado correctamente",
                id
        );

        return convertirResponse(actualizado);
    }

    @Override
    @Transactional
    public void delete(Long id) {

        Cliente cliente =
                clienteRepository.findById(id)
                        .orElseThrow(() ->
                                new RecursoNoEncontradoException(
                                        "Cliente no encontrado con id: " + id
                                )
                        );

        if (!cliente.getEstado()) {
            throw new ReglaNegocioException(
                    "El cliente ya está inactivo: " + id);
        }
        cliente.setEstado(false);
        clienteRepository.save(cliente);

        log.info(
                "Cliente id={} dado de baja correctamente",
                id
        );
    }

    private ClienteResponseDTO convertirResponse(
            Cliente cliente) {

        return new ClienteResponseDTO(
                cliente.getId(),
                cliente.getDni(),
                cliente.getNombres(),
                cliente.getApellidos(),
                cliente.getEmail(),
                cliente.getTelefono(),
                cliente.getDireccion(),
                cliente.getEstado(),
                cliente.getFechaCreacion(),
                cliente.getFechaModificacion()
        );
    }

    private String normalizar(String valor) {

        if (valor == null || valor.isBlank()) {
            return null;
        }

        return valor.trim();
    }
}
