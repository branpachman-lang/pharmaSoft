package pe.com.upeu.PharmaBackend.config;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.cache.Cache;
import org.springframework.cache.concurrent.ConcurrentMapCache;
import org.springframework.cache.concurrent.ConcurrentMapCacheManager;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.data.redis.serializer.JdkSerializationRedisSerializer;
import pe.com.upeu.PharmaBackend.dto.*;
import pe.com.upeu.PharmaBackend.entity.Categoria;
import pe.com.upeu.PharmaBackend.entity.Cliente;
import pe.com.upeu.PharmaBackend.entity.Producto;
import pe.com.upeu.PharmaBackend.entity.Venta;
import pe.com.upeu.PharmaBackend.exception.ReglaNegocioException;
import pe.com.upeu.PharmaBackend.repository.*;
import pe.com.upeu.PharmaBackend.service.impl.*;
import pe.com.upeu.PharmaBackend.service.service.*;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/** Verifica los proxies reales de Spring con repositorios controlados, sin Oracle. */
class CacheCatalogosTest {
    private AnnotationConfigApplicationContext contexto;
    private CategoriaRepository categorias;
    private ProductoRepository productos;
    private ClienteRepository clientes;
    private VentaRepository ventas;
    private CategoriaService servicioCategorias;
    private ProductoService servicioProductos;
    private VentaService servicioVentas;
    private CachePruebaManager cache;

    @BeforeEach
    void preparar() {
        categorias = mock(CategoriaRepository.class);
        productos = mock(ProductoRepository.class);
        clientes = mock(ClienteRepository.class);
        ventas = mock(VentaRepository.class);
        cache = new CachePruebaManager();
        contexto = new AnnotationConfigApplicationContext();
        contexto.registerBean("cacheManager", CachePruebaManager.class, () -> cache);
        contexto.registerBean(CategoriaRepository.class, () -> categorias);
        contexto.registerBean(ProductoRepository.class, () -> productos);
        contexto.registerBean(ClienteRepository.class, () -> clientes);
        contexto.registerBean(VentaRepository.class, () -> ventas);
        contexto.register(CacheConfig.class, CategoriaServiceImpl.class,
                ProductoServiceImpl.class, VentaServiceImpl.class);
        contexto.refresh();
        servicioCategorias = contexto.getBean(CategoriaService.class);
        servicioProductos = contexto.getBean(ProductoService.class);
        servicioVentas = contexto.getBean(VentaService.class);
        when(categorias.findAll(any(Pageable.class)))
                .thenAnswer(i -> new PageImpl<>(List.of(categoria()), i.getArgument(0), 50));
        when(productos.findAll(any(Pageable.class)))
                .thenAnswer(i -> new PageImpl<>(List.of(producto()), i.getArgument(0), 50));
    }

    @AfterEach
    void cerrar() {
        contexto.close();
    }

    @Test
    void repiteLaMismaPaginaSinConsultarElRepositorioYSeparaOtrosParametros() {
        var primera = servicioCategorias.listarPaginado(0, 10, "nombre", "asc");
        assertThat(servicioCategorias.listarPaginado(0, 10, "nombre", "asc")).isSameAs(primera);
        verify(categorias, times(1)).findAll(any(Pageable.class));
        servicioCategorias.listarPaginado(1, 10, "nombre", "asc");
        servicioCategorias.listarPaginado(0, 5, "nombre", "asc");
        servicioCategorias.listarPaginado(0, 10, "id", "asc");
        servicioCategorias.listarPaginado(0, 10, "nombre", "desc");
        verify(categorias, times(5)).findAll(any(Pageable.class));
    }

    @Test
    void crearCategoriaInvalidaLaPaginaAnterior() {
        servicioCategorias.listarPaginado(0, 10, "nombre", "asc");
        when(categorias.save(any(Categoria.class))).thenAnswer(i -> i.getArgument(0));
        servicioCategorias.create(new CategoriaRequestDTO("Nueva categoria", "Prueba", true));
        servicioCategorias.listarPaginado(0, 10, "nombre", "asc");
        verify(categorias, times(2)).findAll(any(Pageable.class));
    }

    @Test
    void renombrarCategoriaInvalidaCategoriasYProductos() {
        servicioCategorias.listarPaginado(0, 10, "nombre", "asc");
        servicioProductos.listarPaginado(0, 10, "nombre", "asc");
        when(categorias.findById(1L)).thenReturn(Optional.of(categoria()));
        when(categorias.save(any(Categoria.class))).thenAnswer(i -> i.getArgument(0));
        servicioCategorias.update(1L, new CategoriaRequestDTO("Nombre nuevo", "Prueba", true));
        servicioCategorias.listarPaginado(0, 10, "nombre", "asc");
        servicioProductos.listarPaginado(0, 10, "nombre", "asc");
        verify(categorias, times(2)).findAll(any(Pageable.class));
        verify(productos, times(2)).findAll(any(Pageable.class));
    }

    @Test
    void unaEscrituraRechazadaNoInvalidaLaCache() {
        servicioCategorias.listarPaginado(0, 10, "nombre", "asc");
        when(categorias.existsByNombreIgnoreCase("Duplicada")).thenReturn(true);
        assertThatThrownBy(() -> servicioCategorias.create(
                new CategoriaRequestDTO("Duplicada", "Prueba", true)))
                .isInstanceOf(ReglaNegocioException.class);
        servicioCategorias.listarPaginado(0, 10, "nombre", "asc");
        verify(categorias, times(1)).findAll(any(Pageable.class));
    }

    @Test
    void unaVentaInvalidaElStockCacheado() {
        servicioProductos.listarPaginado(0, 10, "nombre", "asc");
        servicioProductos.listarPaginado(0, 10, "nombre", "asc");
        Cliente cliente = new Cliente();
        cliente.setId(1L);
        cliente.setEstado(true);
        cliente.setNombres("Ana");
        cliente.setApellidos("Pacho");
        when(clientes.findById(1L)).thenReturn(Optional.of(cliente));
        when(productos.findById(2L)).thenReturn(Optional.of(producto()));
        when(productos.descontarStockSiAlcanza(2L, 1)).thenReturn(1);
        when(ventas.save(any(Venta.class))).thenAnswer(i -> i.getArgument(0));
        servicioVentas.registrar(new VentaRequestDTO(1L, List.of(new DetalleVentaRequestDTO(2L, 1))));
        servicioProductos.listarPaginado(0, 10, "nombre", "asc");
        verify(productos, times(2)).findAll(any(Pageable.class));
    }

    @Test
    void alFallarLecturaYEscrituraDeCacheContinuaConElRepositorio() {
        cache.noDisponible = true;
        assertThat(servicioCategorias.listarPaginado(0, 10, "nombre", "asc").contenido())
                .extracting(CategoriaResponseDTO::getNombre).containsExactly("Analgesicos");
        assertThat(servicioCategorias.listarPaginado(0, 10, "nombre", "asc").contenido()).hasSize(1);
        when(categorias.save(any(Categoria.class))).thenAnswer(i -> i.getArgument(0));
        assertThatCode(() -> servicioCategorias.create(
                new CategoriaRequestDTO("Nueva categoria", "Prueba", true))).doesNotThrowAnyException();
        verify(categorias, times(2)).findAll(any(Pageable.class));
    }

    @Test
    void serializaYRecuperaPaginasConLosDtoReales() {
        var serializador = new JdkSerializationRedisSerializer();
        var categoriasDto = servicioCategorias.listarPaginado(0, 10, "nombre", "asc");
        var productosDto = servicioProductos.listarPaginado(0, 10, "nombre", "asc");
        assertThat(serializador.deserialize(serializador.serialize(categoriasDto)))
                .usingRecursiveComparison().isEqualTo(categoriasDto);
        assertThat(serializador.deserialize(serializador.serialize(productosDto)))
                .usingRecursiveComparison().isEqualTo(productosDto);
    }

    private static Categoria categoria() {
        Categoria categoria = new Categoria();
        categoria.setId(1L);
        categoria.setNombre("Analgesicos");
        categoria.setEstado(true);
        return categoria;
    }

    private static Producto producto() {
        Producto producto = new Producto();
        producto.setId(2L);
        producto.setNombre("Paracetamol");
        producto.setPrecio(new BigDecimal("2.50"));
        producto.setStock(10);
        producto.setEstado(true);
        producto.setCategoria(categoria());
        return producto;
    }

    private static class CachePruebaManager extends ConcurrentMapCacheManager {
        boolean noDisponible;

        @Override
        protected Cache createConcurrentMapCache(String name) {
            return new ConcurrentMapCache(name) {
                private void comprobarDisponibilidad() {
                    if (noDisponible) throw new IllegalStateException("Cache de prueba no disponible");
                }

                @Override public ValueWrapper get(Object key) {
                    comprobarDisponibilidad();
                    return super.get(key);
                }

                @Override public void put(Object key, Object value) {
                    comprobarDisponibilidad();
                    super.put(key, value);
                }

                @Override public void clear() {
                    comprobarDisponibilidad();
                    super.clear();
                }
            };
        }
    }
}
