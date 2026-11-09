package pe.com.upeu.PharmaBackend.config;

import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import pe.com.upeu.PharmaBackend.exception.GlobalExceptionHandler;
import pe.com.upeu.PharmaBackend.exception.ReglaNegocioException;

import static org.assertj.core.api.Assertions.*;

class ErrorRequestIdTest {
    @Test
    void errorDeNegocioConservaElIdGeneradoPorElFiltro() throws Exception {
        var request = new MockHttpServletRequest("POST", "/api/v1/ventas");
        var response = new MockHttpServletResponse();
        new RequestIdFilter().doFilter(request, response, (req, res) -> {
            var error = new GlobalExceptionHandler()
                    .handleBusinessRule(new ReglaNegocioException("Stock insuficiente"), request).getBody();
            assertThat(error).isNotNull();
            assertThat(error.getRequestId()).isEqualTo(response.getHeader("X-Request-Id"));
            assertThat(error.getStatus()).isEqualTo(409);
        });
        assertThat(MDC.get("requestId")).isNull();
    }

    @Test
    void falloInesperadoNoExponeElMensajeInterno() {
        var error = new GlobalExceptionHandler().handleUnexpected(
                new IllegalStateException("dato privado de conexion"),
                new MockHttpServletRequest("GET", "/api/v1/productos")).getBody();
        assertThat(error.getMessage()).isEqualTo("No se pudo completar la operación");
        assertThat(error.getStatus()).isEqualTo(500);
    }

    @Test
    void conservaElEstadoYLaCabeceraAllowDeUnMetodoNoPermitido() {
        var response = new GlobalExceptionHandler().handleUnexpected(
                new org.springframework.web.HttpRequestMethodNotSupportedException("PATCH", java.util.List.of("GET")),
                new MockHttpServletRequest("PATCH", "/api/v1/productos"));
        assertThat(response.getStatusCode().value()).isEqualTo(405);
        assertThat(response.getHeaders().getFirst("Allow")).isEqualTo("GET");
    }
}
