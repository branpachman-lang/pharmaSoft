package pe.com.upeu.PharmaBackend.controller;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import pe.com.upeu.PharmaBackend.dto.ClienteRequestDTO;
import pe.com.upeu.PharmaBackend.dto.ClienteResponseDTO;
import pe.com.upeu.PharmaBackend.service.service.ClienteService;


@RestController
@RequestMapping("/api/v1/clientes")
public class ClienteController {

    private final ClienteService clienteService;

    public ClienteController(
            ClienteService clienteService) {

        this.clienteService = clienteService;
    }

    @PostMapping
    public ResponseEntity<ClienteResponseDTO> create(
            @Valid
            @RequestBody ClienteRequestDTO request) {

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(clienteService.create(request));
    }

    @GetMapping
    public ResponseEntity<Iterable<ClienteResponseDTO>> readAll() {

        return ResponseEntity.ok(
                clienteService.readAll()
        );
    }

    @GetMapping("/{id}")
    public ResponseEntity<ClienteResponseDTO> read(
            @PathVariable Long id) {

        return ResponseEntity.ok(
                clienteService.read(id)
        );
    }

    @PutMapping("/{id}")
    public ResponseEntity<ClienteResponseDTO> update(
            @PathVariable Long id,
            @Valid
            @RequestBody ClienteRequestDTO request) {

        return ResponseEntity.ok(
                clienteService.update(id, request)
        );
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(
            @PathVariable Long id) {

        clienteService.delete(id);

        return ResponseEntity
                .noContent()
                .build();
    }
}