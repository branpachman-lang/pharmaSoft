package pe.com.upeu.PharmaBackend.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import pe.com.upeu.PharmaBackend.entity.Categoria;

public interface CategoriaRepository extends JpaRepository<Categoria, Long> {

}
