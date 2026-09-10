package pe.com.upeu.PharmaBackend.controller;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import pe.com.upeu.PharmaBackend.dto.reporte.ProductoMasVendidoDTO;
import pe.com.upeu.PharmaBackend.dto.reporte.VentaPorCategoriaDTO;
import pe.com.upeu.PharmaBackend.service.service.ReporteService;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/v1/reportes")
public class ReporteController {

    private final ReporteService reporteService;

    public ReporteController(
            ReporteService reporteService) {

        this.reporteService = reporteService;
    }

    /*
     * Total facturado y unidades vendidas por categoría.
     * El rango de fechas es opcional: sin fechas reporta el histórico.
     */
    @GetMapping("/ventas-por-categoria")
    public ResponseEntity<List<VentaPorCategoriaDTO>> ventasPorCategoria(

            @RequestParam(required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate desde,

            @RequestParam(required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate hasta) {

        return ResponseEntity.ok(
                reporteService.ventasPorCategoria(desde, hasta)
        );
    }

    /*
     * Ranking de productos más vendidos, ordenado por unidades.
     */
    @GetMapping("/productos-mas-vendidos")
    public ResponseEntity<List<ProductoMasVendidoDTO>> productosMasVendidos(

            @RequestParam(required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate desde,

            @RequestParam(required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate hasta) {

        return ResponseEntity.ok(
                reporteService.productosMasVendidos(desde, hasta)
        );
    }
}