package pe.com.upeu.PharmaBackend.repository;
import org.springframework.data.jpa.repository.JpaRepository;
import pe.com.upeu.PharmaBackend.entity.Venta;

public interface VentaRepository extends JpaRepository<Venta, Long> {
}