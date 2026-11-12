package pe.com.upeu.PharmaBackend.auditoria;

import org.slf4j.MDC;
import pe.com.upeu.PharmaBackend.config.AuditoriaConfig;

public record EventoAuditoria(String usuario, String accion, String entidad,
                             Long entidadId, String detalle, String requestId) {
    public static EventoAuditoria de(String accion, String entidad, Long id, String detalle) {
        return new EventoAuditoria(AuditoriaConfig.usuarioActual(), accion, entidad, id,
                recortar(detalle, 500), MDC.get("requestId"));
    }

    public static EventoAuditoria login(String accion, String usuario) {
        String nombre = usuario.isBlank() ? "anonimo" : recortar(usuario, 50);
        return new EventoAuditoria(nombre, accion, "Usuario", null, null, MDC.get("requestId"));
    }

    private static String recortar(String texto, int maximo) {
        if (texto == null || texto.codePointCount(0, texto.length()) <= maximo) {
            return texto;
        }
        return texto.substring(0, texto.offsetByCodePoints(0, maximo));
    }
}
