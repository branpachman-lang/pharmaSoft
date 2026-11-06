package pe.com.upeu.PharmaBackend.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cache.Cache;
import org.springframework.cache.annotation.CachingConfigurer;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.interceptor.CacheErrorHandler;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.Ordered;

@Configuration
// La cache envuelve la transaccion: se invalida tras confirmar la escritura.
@EnableCaching(order = Ordered.HIGHEST_PRECEDENCE)
public class CacheConfig implements CachingConfigurer {
    private static final Logger log = LoggerFactory.getLogger(CacheConfig.class);

    @Override
    public CacheErrorHandler errorHandler() {
        return new CacheErrorHandler() {
            @Override
            public void handleCacheGetError(RuntimeException ex, Cache cache, Object key) {
                advertir("leer", cache, ex);
            }

            @Override
            public void handleCachePutError(RuntimeException ex, Cache cache, Object key, Object value) {
                advertir("guardar", cache, ex);
            }

            @Override
            public void handleCacheEvictError(RuntimeException ex, Cache cache, Object key) {
                advertir("invalidar", cache, ex);
            }

            @Override
            public void handleCacheClearError(RuntimeException ex, Cache cache) {
                advertir("limpiar", cache, ex);
            }

            private void advertir(String operacion, Cache cache, RuntimeException ex) {
                // No se escriben valores de la cache ni credenciales de conexion.
                log.warn("Cache {} no disponible al {} | {}. Se continua sin cache",
                        cache.getName(), operacion, ex.getClass().getSimpleName());
            }
        };
    }
}
