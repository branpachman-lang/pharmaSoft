package pe.com.upeu.PharmaBackend.repository;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import pe.com.upeu.PharmaBackend.entity.Producto;

import java.util.List;

public interface ProductoRepository extends JpaRepository<Producto, Long> {

    boolean existsByNombreIgnoreCase(String nombre);
    boolean existsByNombreIgnoreCaseAndIdNot(String nombre, long id);

    List<Producto> findByCategoriaId(Long categoriaId);
    boolean existsByCategoriaId(Long categoriaId);

    @Modifying(flushAutomatically = true)
    @Query("""
            update Producto p
               set p.stock = p.stock - :cantidad
             where p.id = :productoId
               and p.estado = true
               and p.stock >= :cantidad
            """)
    int descontarStockSiAlcanza(@Param("productoId") Long productoId,
                                @Param("cantidad") int cantidad);

}
