package pe.com.upeu.PharmaBackend.dto;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class DetalleVentaRequestDTO {

    @NotNull(
            message = "El producto es obligatorio"
    )
    @Positive(
            message = "El identificador del producto debe ser válido"
    )
    private Long productoId;

    @NotNull(
            message = "La cantidad es obligatoria"
    )
    @Min(
            value = 1,
            message = "La cantidad debe ser mayor que cero"
    )
    private Integer cantidad;
}
