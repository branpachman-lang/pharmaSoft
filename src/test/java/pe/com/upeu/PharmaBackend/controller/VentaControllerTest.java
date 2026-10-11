package pe.com.upeu.PharmaBackend.controller;

import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import pe.com.upeu.PharmaBackend.dto.PaginaResponseDTO;
import pe.com.upeu.PharmaBackend.dto.VentaResponseDTO;
import pe.com.upeu.PharmaBackend.service.service.VentaService;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class VentaControllerTest {
    @Test
    void buscarSinFiltrosDevuelveLaPaginaQueEsperaAngular() throws Exception {
        VentaService servicio = mock(VentaService.class);
        var venta = new VentaResponseDTO(5L, LocalDateTime.of(2026, 10, 11, 12, 0),
                1L, "Ana Pacho", "REGISTRADA", new BigDecimal("16.50"), List.of());
        var pagina = new PaginaResponseDTO<>(List.of(venta), 0, 10, 1, 1, true);
        when(servicio.buscarVentas(isNull(), isNull(), isNull(), isNull(),
                eq(0), eq(10), eq("fecha"), eq("desc"))).thenReturn(pagina);
        when(servicio.listar()).thenReturn(List.of(venta));

        var mvc = MockMvcBuilders.standaloneSetup(new VentaController(servicio)).build();
        mvc.perform(get("/api/v1/ventas/buscar"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElementos").value(1))
                .andExpect(jsonPath("$.contenido[0].id").value(5))
                .andExpect(jsonPath("$.contenido[0].clienteNombre").value("Ana Pacho"));
        mvc.perform(get("/api/v1/ventas"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(5));
    }
}
