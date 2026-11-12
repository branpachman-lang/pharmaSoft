package pe.com.upeu.PharmaBackend.auditoria;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;
import pe.com.upeu.PharmaBackend.service.service.AuditoriaService;

@Component
public class AuditoriaListener {
    private static final Logger log = LoggerFactory.getLogger(AuditoriaListener.class);

    private final AuditoriaService auditoria;

    public AuditoriaListener(AuditoriaService auditoria) {
        this.auditoria = auditoria;
    }

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void alConfirmar(EventoAuditoria evento) {
        registrar(evento);
    }

    public void registrar(EventoAuditoria evento) {
        try {
            auditoria.registrar(evento);
        } catch (RuntimeException ex) {
            log.error("No se pudo guardar auditoría | accion={} | entidadId={} | error={}",
                    evento.accion(), evento.entidadId(), ex.getClass().getSimpleName());
        }
    }
}
