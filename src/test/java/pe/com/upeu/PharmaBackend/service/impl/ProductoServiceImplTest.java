package pe.com.upeu.PharmaBackend.service.impl;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import pe.com.upeu.PharmaBackend.dto.PaginaResponseDTO;
import pe.com.upeu.PharmaBackend.dto.ProductoRequestDTO;
import pe.com.upeu.PharmaBackend.dto.ProductoResponseDTO;
import pe.com.upeu.PharmaBackend.entity.Categoria;
import pe.com.upeu.PharmaBackend.entity.Producto;
import pe.com.upeu.PharmaBackend.exception.ReglaNegocioException;
import pe.com.upeu.PharmaBackend.repository.CategoriaRepository;
import pe.com.upeu.PharmaBackend.repository.ProductoRepository;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ProductoServiceImplTest {
    @Mock ProductoRepository productoRepository;
    @Mock CategoriaRepository categoriaRepository;
    @InjectMocks ProductoServiceImpl servicio;

    private Categoria categoria;
    private Producto producto;

    @BeforeEach
    void preparar() {
        categoria = new Categoria();
        categoria.setId(3L);
        categoria.setNombre("Analgésicos");
        categoria.setEstado(true);
        producto = new Producto();
        producto.setId(8L);
        producto.setNombre("Paracetamol");
        producto.setCategoria(categoria);
        producto.setPrecio(new BigDecimal("5.50"));
        producto.setStock(12);
        producto.setEstado(true);
    }

    @Test
    void bajaLogicaConservaElProducto() {
        when(productoRepository.findById(8L)).thenReturn(Optional.of(producto));

        servicio.delete(8L);

        assertFalse(producto.getEstado());
        verify(productoRepository).save(producto);
        verify(productoRepository, never()).delete(any(Producto.class));
    }

    @Test
    void noPermiteBajaDeProductoInactivo() {
        producto.setEstado(false);
        when(productoRepository.findById(8L)).thenReturn(Optional.of(producto));

        assertThrows(ReglaNegocioException.class, () -> servicio.delete(8L));
        verify(productoRepository, never()).save(any(Producto.class));
    }

    @Test
    void noPermiteCrearConCategoriaInactiva() {
        categoria.setEstado(false);
        var solicitud = new ProductoRequestDTO("Nuevo producto", null,
                new BigDecimal("1.50"), 2, true, 3L);
        when(categoriaRepository.findById(3L)).thenReturn(Optional.of(categoria));

        assertThrows(ReglaNegocioException.class, () -> servicio.create(solicitud));
        verify(productoRepository, never()).save(any(Producto.class));
    }

    @Test
    void paginaYConservaElNombreDeLaCategoria() {
        when(productoRepository.findAll(any(Pageable.class)))
                .thenReturn(new PageImpl<>(List.of(producto)));

        PaginaResponseDTO<ProductoResponseDTO> pagina =
                servicio.listarPaginado(0, 5, "nombre", "asc");

        assertEquals(1, pagina.totalElementos());
        assertEquals("Analgésicos", pagina.contenido().getFirst().getCategoriaNombre());
        verify(productoRepository).findAll(any(Pageable.class));
    }

    @Test
    void rechazaCamposDeOrdenNoPermitidos() {
        assertThrows(ReglaNegocioException.class,
                () -> servicio.listarPaginado(0, 10, "categoria", "asc"));
        verifyNoInteractions(productoRepository);
    }
}
