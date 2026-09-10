package pe.com.upeu.PharmaBackend.service.impl;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pe.com.upeu.PharmaBackend.dto.reporte.ProductoMasVendidoDTO;
import pe.com.upeu.PharmaBackend.dto.reporte.VentaPorCategoriaDTO;
import pe.com.upeu.PharmaBackend.exception.ReglaNegocioException;
import pe.com.upeu.PharmaBackend.repository.VentaRepository;
import pe.com.upeu.PharmaBackend.service.service.ReporteService;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;

@Service
public class ReporteServiceImpl implements ReporteService {

    private static final Logger log =
            LoggerFactory.getLogger(ReporteServiceImpl.class);

    private final VentaRepository ventaRepository;

    public ReporteServiceImpl(
            VentaRepository ventaRepository) {

        this.ventaRepository = ventaRepository;
    }

    @Override
    @Transactional(readOnly = true)
    public List<VentaPorCategoriaDTO> ventasPorCategoria(
            LocalDate desde,
            LocalDate hasta) {

        long inicio = System.currentTimeMillis();

        log.info("Inicio reporte ventas por categoria | desde={} | hasta={}",
                desde, hasta);

        validarRango(desde, hasta);

        List<VentaPorCategoriaDTO> resultado =
                ventaRepository.reporteVentasPorCategoria(
                        inicioDelDia(desde),
                        finDelDia(hasta)
                );

        log.info("Fin reporte ventas por categoria | desde={} | hasta={} | "
                        + "filas={} | duracionMs={}",
                desde, hasta,
                resultado.size(),
                System.currentTimeMillis() - inicio);

        return resultado;
    }

    @Override
    @Transactional(readOnly = true)
    public List<ProductoMasVendidoDTO> productosMasVendidos(
            LocalDate desde,
            LocalDate hasta) {

        long inicio = System.currentTimeMillis();

        log.info("Inicio reporte productos mas vendidos | desde={} | hasta={}",
                desde, hasta);

        validarRango(desde, hasta);

        List<ProductoMasVendidoDTO> resultado =
                ventaRepository.reporteProductosMasVendidos(
                        inicioDelDia(desde),
                        finDelDia(hasta)
                );

        log.info("Fin reporte productos mas vendidos | desde={} | hasta={} | "
                        + "filas={} | duracionMs={}",
                desde, hasta,
                resultado.size(),
                System.currentTimeMillis() - inicio);

        return resultado;
    }

    private void validarRango(LocalDate desde, LocalDate hasta) {

        if (desde != null
                && hasta != null
                && desde.isAfter(hasta)) {

            throw new ReglaNegocioException(
                    "El rango de fechas es inválido: 'desde' ("
                            + desde
                            + ") es posterior a 'hasta' ("
                            + hasta + ")");
        }
    }

    private LocalDateTime inicioDelDia(LocalDate fecha) {

        return (fecha == null)
                ? null
                : fecha.atStartOfDay();
    }

    private LocalDateTime finDelDia(LocalDate fecha) {

        return (fecha == null)
                ? null
                : fecha.atTime(LocalTime.MAX);
    }
}