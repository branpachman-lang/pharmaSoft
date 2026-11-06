package pe.com.upeu.PharmaBackend.dto;

import java.util.List;
import java.io.Serializable;

public record PaginaResponseDTO<T>(
        List<T> contenido,
        int pagina,
        int tamanio,
        long totalElementos,
        int totalPaginas,
        boolean ultima
) implements Serializable {
    private static final long serialVersionUID = 1L;
}
