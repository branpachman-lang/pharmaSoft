package pe.com.upeu.PharmaBackend.controller;

import jakarta.validation.Valid;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import pe.com.upeu.PharmaBackend.dto.VentaRequestDTO;
import pe.com.upeu.PharmaBackend.dto.VentaResponseDTO;
import pe.com.upeu.PharmaBackend.dto.PaginaResponseDTO;
import pe.com.upeu.PharmaBackend.enums.EstadoVenta;
import pe.com.upeu.PharmaBackend.service.service.VentaService;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/v1/ventas")
public class VentaController {

    private final VentaService ventaService;

    public VentaController(
            VentaService ventaService) {

        this.ventaService = ventaService;
    }

    @PostMapping
    public ResponseEntity<VentaResponseDTO> registrar(
            @Valid
            @RequestBody VentaRequestDTO request) {

        VentaResponseDTO response =
                ventaService.registrar(request);

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(response);
    }

    @GetMapping("/{id}")
    public ResponseEntity<VentaResponseDTO> buscar(
            @PathVariable Long id) {

        return ResponseEntity.ok(
                ventaService.buscar(id)
        );
    }

    @GetMapping
    public ResponseEntity<List<VentaResponseDTO>> listar() {

        return ResponseEntity.ok(
                ventaService.listar()
        );
    }

    /*
     * Búsqueda de ventas con filtros combinados.
     *
     * Todos los filtros son opcionales. Sin filtros se devuelven todas
     * las ventas, y sin coincidencias una página con contenido vacío.
     */
    @GetMapping("/buscar")
    public ResponseEntity<PaginaResponseDTO<VentaResponseDTO>> buscar(

            @RequestParam(required = false)
            Long clienteId,

            @RequestParam(required = false)
            EstadoVenta estado,

            @RequestParam(required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate desde,

            @RequestParam(required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate hasta,

            @RequestParam(defaultValue = "0")
            int pagina,

            @RequestParam(defaultValue = "10")
            int tamanio,

            @RequestParam(required = false, defaultValue = "fecha")
            String ordenarPor,

            @RequestParam(required = false, defaultValue = "desc")
            String direccion) {

        return ResponseEntity.ok(
                ventaService.buscarVentas(
                        clienteId,
                        estado,
                        desde,
                        hasta,
                        pagina,
                        tamanio,
                        ordenarPor,
                        direccion
                )
        );
    }
}
