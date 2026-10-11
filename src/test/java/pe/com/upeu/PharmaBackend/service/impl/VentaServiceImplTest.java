package pe.com.upeu.PharmaBackend.service.impl;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import pe.com.upeu.PharmaBackend.dto.DetalleVentaRequestDTO;
import pe.com.upeu.PharmaBackend.dto.VentaRequestDTO;
import pe.com.upeu.PharmaBackend.entity.Cliente;
import pe.com.upeu.PharmaBackend.entity.Producto;
import pe.com.upeu.PharmaBackend.entity.Venta;
import pe.com.upeu.PharmaBackend.enums.EstadoVenta;
import pe.com.upeu.PharmaBackend.exception.ReglaNegocioException;
import pe.com.upeu.PharmaBackend.repository.ClienteRepository;
import pe.com.upeu.PharmaBackend.repository.ProductoRepository;
import pe.com.upeu.PharmaBackend.repository.VentaRepository;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class VentaServiceImplTest {
    @Mock VentaRepository ventas;
    @Mock ClienteRepository clientes;
    @Mock ProductoRepository productos;
    @InjectMocks VentaServiceImpl servicio;

    private final Cliente cliente = cliente();
    private final Producto producto = producto();

    @Test
    void registraDetalleConPrecioDelServidorYDescuentoCondicional() {
        when(clientes.findById(1L)).thenReturn(Optional.of(cliente));
        when(productos.findById(2L)).thenReturn(Optional.of(producto));
        when(productos.descontarStockSiAlcanza(2L, 3)).thenReturn(1);
        when(ventas.save(any(Venta.class))).thenAnswer(invocacion -> {
            Venta venta = invocacion.getArgument(0);
            venta.setId(9L);
            return venta;
        });

        var resultado = servicio.registrar(new VentaRequestDTO(1L,
                List.of(new DetalleVentaRequestDTO(2L, 3))));

        assertEquals(new BigDecimal("16.50"), resultado.getTotal());
        assertEquals(new BigDecimal("5.50"), resultado.getDetalles().getFirst().getPrecio());
        assertEquals(new BigDecimal("16.50"), resultado.getDetalles().getFirst().getSubtotal());
        assertEquals(EstadoVenta.REGISTRADA.name(), resultado.getEstado());
        verify(productos).descontarStockSiAlcanza(2L, 3);
        verify(ventas).save(any(Venta.class));
    }

    @Test
    void noGuardaSiElStockActualYaNoAlcanza() {
        when(clientes.findById(1L)).thenReturn(Optional.of(cliente));
        when(productos.findById(2L)).thenReturn(Optional.of(producto));
        when(productos.descontarStockSiAlcanza(2L, 20)).thenReturn(0);

        var error = assertThrows(ReglaNegocioException.class,
                () -> servicio.registrar(new VentaRequestDTO(1L,
                        List.of(new DetalleVentaRequestDTO(2L, 20)))));

        assertTrue(error.getMessage().contains("Stock insuficiente"));
        verify(ventas, never()).save(any(Venta.class));
    }

    @Test
    void buscaConPaginacionYOrdenEstable() {
        Venta venta = new Venta();
        venta.setId(9L);
        venta.setCliente(cliente);
        venta.setFecha(LocalDateTime.of(2026, 10, 11, 12, 0));
        venta.setEstado(EstadoVenta.REGISTRADA);
        venta.setTotal(new BigDecimal("16.50"));
        when(ventas.findAll(any(Specification.class), any(Pageable.class)))
                .thenReturn(new PageImpl<>(List.of(venta),
                        org.springframework.data.domain.PageRequest.of(1, 5), 6));

        var resultado = servicio.buscarVentas(1L, EstadoVenta.REGISTRADA,
                LocalDate.of(2026, 10, 1), LocalDate.of(2026, 10, 31),
                1, 5, "fecha", "desc");

        assertEquals(1, resultado.pagina());
        assertEquals(2, resultado.totalPaginas());
        assertEquals(6, resultado.totalElementos());
        assertEquals(9L, resultado.contenido().getFirst().getId());
        ArgumentCaptor<Pageable> captor = ArgumentCaptor.forClass(Pageable.class);
        verify(ventas).findAll(any(Specification.class), captor.capture());
        assertEquals(1, captor.getValue().getPageNumber());
        assertEquals(5, captor.getValue().getPageSize());
        assertEquals("fecha: DESC,id: DESC", captor.getValue().getSort().toString());
    }

    @Test
    void rechazaRangoInvertidoSinConsultarLaBase() {
        assertThrows(ReglaNegocioException.class,
                () -> servicio.buscarVentas(null, null, LocalDate.of(2026, 10, 12),
                        LocalDate.of(2026, 10, 11), 0, 10, "fecha", "desc"));
        verifyNoInteractions(ventas);
    }

    private static Cliente cliente() {
        Cliente cliente = new Cliente();
        cliente.setId(1L);
        cliente.setNombres("Ana");
        cliente.setApellidos("Pacho");
        cliente.setEstado(true);
        return cliente;
    }

    private static Producto producto() {
        Producto producto = new Producto();
        producto.setId(2L);
        producto.setNombre("Paracetamol");
        producto.setPrecio(new BigDecimal("5.50"));
        producto.setStock(10);
        producto.setEstado(true);
        return producto;
    }
}
