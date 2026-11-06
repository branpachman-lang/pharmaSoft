package pe.com.upeu.PharmaBackend.config;

import jakarta.servlet.ServletException;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import static org.assertj.core.api.Assertions.*;

class RequestIdFilterTest {
    private final RequestIdFilter filtro = new RequestIdFilter();

    @Test
    void devuelveElMismoIdDelContextoYLoLimpiaAlFinal() throws Exception {
        var request = new MockHttpServletRequest("GET", "/api/v1/categorias");
        var response = new MockHttpServletResponse();
        filtro.doFilter(request, response, (req, res) -> {
            assertThat(MDC.get(RequestIdFilter.CLAVE_MDC))
                    .isEqualTo(response.getHeader(RequestIdFilter.CABECERA))
                    .matches("[0-9a-f]{8}");
            response.setStatus(403);
        });
        assertThat(response.getStatus()).isEqualTo(403);
        assertThat(MDC.get(RequestIdFilter.CLAVE_MDC)).isNull();
    }

    @Test
    void tambienLimpiaElContextoSiLaPeticionFalla() {
        var request = new MockHttpServletRequest("GET", "/api/v1/productos");
        var response = new MockHttpServletResponse();
        assertThatThrownBy(() -> filtro.doFilter(request, response, (req, res) -> {
            throw new ServletException("Fallo controlado");
        })).isInstanceOf(ServletException.class);
        assertThat(response.getHeader(RequestIdFilter.CABECERA)).matches("[0-9a-f]{8}");
        assertThat(MDC.get(RequestIdFilter.CLAVE_MDC)).isNull();
    }
}
