package pe.com.upeu.PharmaBackend.dto;

import java.time.LocalDateTime;
import pe.com.upeu.PharmaBackend.entity.AuditoriaEvento;

public record AuditoriaEventoDTO(Long id, LocalDateTime fecha, String usuario, String accion,
                                 String entidad, Long entidadId, String detalle, String requestId) {
    public static AuditoriaEventoDTO de(AuditoriaEvento evento) {
        return new AuditoriaEventoDTO(evento.getId(), evento.getFecha(), evento.getUsuario(),
                evento.getAccion(), evento.getEntidad(), evento.getEntidadId(),
                evento.getDetalle(), evento.getRequestId());
    }
}
