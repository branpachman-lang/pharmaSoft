package pe.com.upeu.PharmaBackend.service.impl;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pe.com.upeu.PharmaBackend.dto.CategoriaRequestDTO;
import pe.com.upeu.PharmaBackend.dto.CategoriaResponseDTO;
import pe.com.upeu.PharmaBackend.dto.PaginaResponseDTO;
import pe.com.upeu.PharmaBackend.entity.Categoria;
import pe.com.upeu.PharmaBackend.exception.RecursoNoEncontradoException;
import pe.com.upeu.PharmaBackend.exception.ReglaNegocioException;
import pe.com.upeu.PharmaBackend.repository.CategoriaRepository;
import pe.com.upeu.PharmaBackend.repository.ProductoRepository;
import pe.com.upeu.PharmaBackend.service.service.CategoriaService;
import java.util.Set;


@Service
public class CategoriaServiceImpl implements CategoriaService {

    private static final Set<String> CAMPOS_ORDENABLES = Set.of("id", "nombre", "estado");

    private final CategoriaRepository categoriaRepository;
    private final ProductoRepository productoRepository;
    public CategoriaServiceImpl(CategoriaRepository categoriaRepository, ProductoRepository productoRepository) {
        this.categoriaRepository = categoriaRepository;
        this.productoRepository = productoRepository;
    }

    @Override
    @Transactional
    public CategoriaResponseDTO create(CategoriaRequestDTO t) {
        String nombre = t.getNombre().trim();
        if(categoriaRepository.existsByNombreIgnoreCase(nombre)) {
            throw new ReglaNegocioException("Ya existe una categoria con el nombre: " + nombre);
        }
        Categoria categoria = new Categoria();
        categoria.setNombre(nombre);
        categoria.setDescripcion(t.getDescripcion());
        categoria.setEstado(t.getEstado());
        Categoria catCreada = categoriaRepository.save(categoria);

        return convertirResponse(catCreada);
    }

    @Override
    @Transactional
    public CategoriaResponseDTO update(Long aLong, CategoriaRequestDTO t) {

        Categoria categoria = categoriaRepository.findById(aLong).orElseThrow(()->
        new RecursoNoEncontradoException("Categoria no encontrada con el ID: " + aLong)
        );
        categoria.setNombre(t.getNombre());
        categoria.setDescripcion(t.getDescripcion());
        categoria.setEstado(t.getEstado());
        Categoria catActualizada = categoriaRepository.save(categoria);

        return convertirResponse(catActualizada);
    }

    @Override
    @Transactional(readOnly = true)
    public CategoriaResponseDTO read(Long aLong) {
        Categoria categoria = categoriaRepository.findById(aLong).
                orElseThrow(()->
        new RecursoNoEncontradoException("Categoria no encontrada con el ID: " + aLong));
        return convertirResponse(categoria);
    }

    @Override
    @Transactional
    public void delete(Long id) {
        Categoria categoria = categoriaRepository.findById(id)
                .orElseThrow(() -> new RecursoNoEncontradoException(
                        "Categoria no encontrada con el ID: " + id
                ));

        if (!categoria.getEstado()) {
            throw new ReglaNegocioException("La categoría ya está inactiva: " + id);
        }
        if (productoRepository.existsByCategoriaId(id)) {
            throw new ReglaNegocioException(
                    "No se puede eliminar la categoría porque tiene productos asociados"
            );
        }
        categoria.setEstado(false);
        categoriaRepository.save(categoria);
    }

    @Override
    @Transactional(readOnly = true)
    public Iterable<CategoriaResponseDTO> readAll() {
        return categoriaRepository.findAll().
                stream().
                map(this::convertirResponse).
                toList();
    }

    @Transactional(readOnly = true)
    public PaginaResponseDTO<CategoriaResponseDTO> listarPaginado(
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
        Page<Categoria> resultado = categoriaRepository.findAll(PageRequest.of(pagina, tamanio, sort));
        return new PaginaResponseDTO<>(
                resultado.getContent().stream().map(this::convertirResponse).toList(),
                resultado.getNumber(), resultado.getSize(), resultado.getTotalElements(),
                resultado.getTotalPages(), resultado.isLast());
    }

    private CategoriaResponseDTO convertirResponse(Categoria categoria) {
        return  new CategoriaResponseDTO(
                categoria.getId(),
                categoria.getNombre(),
                categoria.getDescripcion(),
                categoria.getEstado(),
                categoria.getFechaCreacion(),
                categoria.getFechaModificacion()
        );
    }
}
