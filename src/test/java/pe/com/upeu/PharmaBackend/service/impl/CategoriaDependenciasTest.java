package pe.com.upeu.PharmaBackend.service.impl;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import pe.com.upeu.PharmaBackend.entity.Categoria;
import pe.com.upeu.PharmaBackend.exception.ReglaNegocioException;
import pe.com.upeu.PharmaBackend.repository.CategoriaRepository;
import pe.com.upeu.PharmaBackend.repository.ProductoRepository;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class CategoriaDependenciasTest {
    @Mock CategoriaRepository categoriaRepository;
    @Mock ProductoRepository productoRepository;
    @InjectMocks CategoriaServiceImpl servicio;

    private Categoria categoria;

    @BeforeEach
    void preparar() {
        categoria = new Categoria();
        categoria.setId(4L);
        categoria.setNombre("Abarrotes");
        categoria.setEstado(true);
    }

    @Test
    void noPermiteBajaCuandoHayProductosAsociados() {
        when(categoriaRepository.findById(4L)).thenReturn(Optional.of(categoria));
        when(productoRepository.existsByCategoriaId(4L)).thenReturn(true);

        ReglaNegocioException error =
                assertThrows(ReglaNegocioException.class, () -> servicio.delete(4L));

        assertTrue(error.getMessage().contains("productos asociados"));
        assertTrue(categoria.getEstado());
        verify(categoriaRepository, never()).save(categoria);
    }

    @Test
    void bajaLogicaCuandoNoHayProductos() {
        when(categoriaRepository.findById(4L)).thenReturn(Optional.of(categoria));

        servicio.delete(4L);

        assertFalse(categoria.getEstado());
        verify(categoriaRepository).save(categoria);
        verify(categoriaRepository, never()).delete(categoria);
    }
}
