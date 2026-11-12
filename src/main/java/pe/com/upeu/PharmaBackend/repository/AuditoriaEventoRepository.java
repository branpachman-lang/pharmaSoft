package pe.com.upeu.PharmaBackend.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import pe.com.upeu.PharmaBackend.entity.AuditoriaEvento;

public interface AuditoriaEventoRepository
        extends JpaRepository<AuditoriaEvento, Long>, JpaSpecificationExecutor<AuditoriaEvento> {
}
