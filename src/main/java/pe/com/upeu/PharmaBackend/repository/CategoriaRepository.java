package pe.com.upeu.PharmaBackend.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import pe.com.upeu.PharmaBackend.entity.Categoria;

public interface CategoriaRepository extends JpaRepository<Categoria, Long> {
    org.springframework.data.domain.Page<Categoria> findByEstadoTrue(org.springframework.data.domain.Pageable pageable);
    boolean existsByNombreIgnoreCase(String nombre);
    boolean existsByNombreIgnoreCaseAndIdNot(String nombre,long id);
}
