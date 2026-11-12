package pe.com.upeu.PharmaBackend.dto;

import java.util.List;
import java.io.Serializable;
import org.springframework.data.domain.Page;

public record PaginaResponseDTO<T>(
        List<T> contenido,
        int pagina,
        int tamanio,
        long totalElementos,
        int totalPaginas,
        boolean ultima
) implements Serializable {
    private static final long serialVersionUID = 1L;

    public static <T> PaginaResponseDTO<T> de(Page<T> pagina) {
        return new PaginaResponseDTO<>(pagina.getContent(), pagina.getNumber(), pagina.getSize(),
                pagina.getTotalElements(), pagina.getTotalPages(), pagina.isLast());
    }
}
