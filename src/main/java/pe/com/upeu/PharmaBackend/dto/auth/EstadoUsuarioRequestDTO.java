package pe.com.upeu.PharmaBackend.dto.auth;

import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class EstadoUsuarioRequestDTO {
    @NotNull(message = "El estado es obligatorio")
    private Boolean estado;
}
