package pe.com.upeu.PharmaBackend.service.impl;

import jakarta.persistence.criteria.Predicate;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import pe.com.upeu.PharmaBackend.auditoria.EventoAuditoria;
import pe.com.upeu.PharmaBackend.dto.AuditoriaEventoDTO;
import pe.com.upeu.PharmaBackend.dto.PaginaResponseDTO;
import pe.com.upeu.PharmaBackend.entity.AuditoriaEvento;
import pe.com.upeu.PharmaBackend.exception.ReglaNegocioException;
import pe.com.upeu.PharmaBackend.repository.AuditoriaEventoRepository;
import pe.com.upeu.PharmaBackend.service.service.AuditoriaService;

@Service
public class AuditoriaServiceImpl implements AuditoriaService {
    private final AuditoriaEventoRepository repository;

    public AuditoriaServiceImpl(AuditoriaEventoRepository repository) {
        this.repository = repository;
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void registrar(EventoAuditoria evento) {
        AuditoriaEvento registro = new AuditoriaEvento();
        registro.setFecha(LocalDateTime.now());
        registro.setUsuario(evento.usuario());
        registro.setAccion(evento.accion());
        registro.setEntidad(evento.entidad());
        registro.setEntidadId(evento.entidadId());
        registro.setDetalle(evento.detalle());
        registro.setRequestId(evento.requestId());
        repository.save(registro);
    }

    @Override
    @Transactional(readOnly = true)
    public PaginaResponseDTO<AuditoriaEventoDTO> buscar(
            String usuario, String accion, LocalDate desde, LocalDate hasta, int pagina, int tamanio) {
        if (pagina < 0 || tamanio < 1 || tamanio > 100) {
            throw new ReglaNegocioException("La página debe ser no negativa y el tamaño debe estar entre 1 y 100");
        }
        if (desde != null && hasta != null && desde.isAfter(hasta)) {
            throw new ReglaNegocioException("La fecha inicial no puede ser posterior a la fecha final");
        }

        Specification<AuditoriaEvento> filtros = (raiz, consulta, criterios) -> {
            List<Predicate> condiciones = new ArrayList<>();
            if (usuario != null && !usuario.isBlank()) {
                condiciones.add(criterios.equal(criterios.upper(raiz.get("usuario")),
                        usuario.strip().toUpperCase(Locale.ROOT)));
            }
            if (accion != null && !accion.isBlank()) {
                condiciones.add(criterios.equal(raiz.get("accion"), accion.strip()));
            }
            if (desde != null) {
                condiciones.add(criterios.greaterThanOrEqualTo(raiz.get("fecha"), desde.atStartOfDay()));
            }
            if (hasta != null) {
                condiciones.add(criterios.lessThan(raiz.get("fecha"), hasta.plusDays(1).atStartOfDay()));
            }
            return criterios.and(condiciones.toArray(Predicate[]::new));
        };
        var solicitud = PageRequest.of(pagina, tamanio, Sort.by(Sort.Direction.DESC, "fecha", "id"));
        return PaginaResponseDTO.de(repository.findAll(filtros, solicitud).map(AuditoriaEventoDTO::de));
    }
}
