package pe.com.upeu.PharmaBackend.service.impl;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pe.com.upeu.PharmaBackend.dto.ProductoRequestDTO;
import pe.com.upeu.PharmaBackend.dto.ProductoResponseDTO;
import pe.com.upeu.PharmaBackend.dto.PaginaResponseDTO;
import pe.com.upeu.PharmaBackend.entity.Categoria;
import pe.com.upeu.PharmaBackend.entity.Producto;
import pe.com.upeu.PharmaBackend.exception.RecursoNoEncontradoException;
import pe.com.upeu.PharmaBackend.exception.ReglaNegocioException;
import pe.com.upeu.PharmaBackend.repository.CategoriaRepository;
import pe.com.upeu.PharmaBackend.repository.ProductoRepository;
import pe.com.upeu.PharmaBackend.service.service.ProductoService;

import java.util.Set;

@Service
public class ProductoServiceImpl implements ProductoService {
    private static final Set<String> CAMPOS_ORDENABLES = Set.of("id", "nombre", "precio", "stock");

    private final ProductoRepository productoRepository;
    private final CategoriaRepository categoriaRepository;

    public ProductoServiceImpl(ProductoRepository productoRepository, CategoriaRepository categoriaRepository) {
        this.productoRepository = productoRepository;
        this.categoriaRepository = categoriaRepository;
    }

    @Override
    @Transactional
    public ProductoResponseDTO create(ProductoRequestDTO t) {
        String nombre = t.getNombre().trim();
        if(productoRepository.existsByNombreIgnoreCase(nombre)) {
            throw new ReglaNegocioException("Ya existe un producto con el nombre: " + nombre);
        }
        Categoria categoria = categoriaRepository.findById(t.getCategoriaId()).orElseThrow(() ->
                new RecursoNoEncontradoException("Categoría no encontrada con el ID: " + t.getCategoriaId())
        );
        validarCategoriaActiva(categoria);
        Producto producto = new Producto();
        producto.setNombre(nombre);
        producto.setDescripcion(t.getDescripcion());
        producto.setPrecio(t.getPrecio());
        producto.setStock(t.getStock());
        producto.setEstado(t.getEstado());
        producto.setCategoria(categoria); // Asignamos la relación

        Producto productoCreado = productoRepository.save(producto);
        return convertirResponse(productoCreado);
    }

    @Override
    @Transactional
    public ProductoResponseDTO update(Long id, ProductoRequestDTO t) {
        Producto producto = productoRepository.findById(id).orElseThrow(() ->
                new RecursoNoEncontradoException("Producto no encontrado con el ID: " + id)
        );

        String nombre = t.getNombre().trim();
        if (productoRepository.existsByNombreIgnoreCaseAndIdNot(nombre, id)) {
            throw new ReglaNegocioException("Ya existe otro producto con el nombre: " + nombre);
        }

        Categoria categoria = categoriaRepository.findById(t.getCategoriaId()).orElseThrow(() ->
                new RecursoNoEncontradoException("Categoría no encontrada con el ID: " + t.getCategoriaId())
        );
        validarCategoriaActiva(categoria);

        producto.setNombre(nombre);
        producto.setDescripcion(t.getDescripcion());
        producto.setPrecio(t.getPrecio());
        producto.setStock(t.getStock());
        producto.setEstado(t.getEstado());
        producto.setCategoria(categoria);

        Producto productoActualizado = productoRepository.save(producto);
        return convertirResponse(productoActualizado);
    }

    @Override
    @Transactional(readOnly = true)
    public ProductoResponseDTO read(Long id) {
        Producto producto = productoRepository.findById(id).orElseThrow(() ->
                new RecursoNoEncontradoException("Producto no encontrado con el ID: " + id)
        );
        return convertirResponse(producto);
    }

    @Override
    @Transactional
    public void delete(Long id) {
        Producto producto = productoRepository.findById(id).orElseThrow(() ->
                new RecursoNoEncontradoException("Producto no encontrado con el ID: " + id)
        );
        if (!producto.getEstado()) {
            throw new ReglaNegocioException("El producto ya está inactivo: " + id);
        }
        producto.setEstado(false);
        productoRepository.save(producto);
    }

    @Override
    @Transactional(readOnly = true)
    public Iterable<ProductoResponseDTO> readAll() {
        return productoRepository.findAll().stream()
                .map(this::convertirResponse)
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public PaginaResponseDTO<ProductoResponseDTO> listarPaginado(
            int pagina, int tamanio, String ordenarPor, String direccion) {
        if (pagina < 0 || tamanio < 1) {
            throw new ReglaNegocioException("La página debe ser mayor o igual a 0 y el tamaño mayor que 0");
        }
        if (!CAMPOS_ORDENABLES.contains(ordenarPor)) {
            throw new ReglaNegocioException("Campo de ordenamiento no permitido: " + ordenarPor);
        }
        if (!direccion.equalsIgnoreCase("asc") && !direccion.equalsIgnoreCase("desc")) {
            throw new ReglaNegocioException("La dirección debe ser asc o desc");
        }
        Sort sort = direccion.equalsIgnoreCase("asc")
                ? Sort.by(ordenarPor).ascending() : Sort.by(ordenarPor).descending();
        if (!ordenarPor.equals("id")) sort = sort.and(Sort.by("id"));
        Page<Producto> resultado = productoRepository.findAll(PageRequest.of(pagina, tamanio, sort));
        return new PaginaResponseDTO<>(
                resultado.getContent().stream().map(this::convertirResponse).toList(),
                resultado.getNumber(), resultado.getSize(), resultado.getTotalElements(),
                resultado.getTotalPages(), resultado.isLast());
    }

    private void validarCategoriaActiva(Categoria categoria) {
        if (!categoria.getEstado()) {
            throw new ReglaNegocioException("La categoría seleccionada está inactiva");
        }
    }

    private ProductoResponseDTO convertirResponse(Producto producto) {
        return new ProductoResponseDTO(
                producto.getId(),
                producto.getNombre(),
                producto.getDescripcion(),
                producto.getPrecio(),
                producto.getStock(),
                producto.getEstado(),
                producto.getCategoria().getId(),
                producto.getCategoria().getNombre(),
                producto.getFechaCreacion(),
                producto.getFechaModificacion()
        );
    }
}
