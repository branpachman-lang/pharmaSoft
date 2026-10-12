package pe.com.upeu.PharmaBackend.dto.reporte;

import java.math.BigDecimal;

public record VentaPorCategoriaDTO(Long categoriaId,
                                   String categoriaNombre,
                                   Long cantidadVendida,
                                   BigDecimal montoTotal) {

}
