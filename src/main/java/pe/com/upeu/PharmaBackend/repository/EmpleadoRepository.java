package pe.com.upeu.PharmaBackend.repository;
import org.springframework.data.jpa.repository.JpaRepository;
import pe.com.upeu.PharmaBackend.entity.Empleado;
public interface EmpleadoRepository extends JpaRepository<Empleado, Long> {
}