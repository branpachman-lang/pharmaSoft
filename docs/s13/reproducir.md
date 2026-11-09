# Repetir las mediciones S13

Trabajar sobre Oracle de ensayo. El script crea una categoría, un producto con stock 10 y un cliente sintético. La venta real de prueba queda en el historial; no borrar una venta ya registrada. Los IDs se guardan en `C-fixtures.json`. No usa ni modifica productos reales.

Requisitos: Java 21, dependencias Maven, Node, dependencias Angular (`npm ci`), Chrome y Playwright. Configurar `PLAYWRIGHT_MODULE` a la carpeta instalada de Playwright si no se resuelve automáticamente. Configurar `S13_USER` y `S13_PASSWORD` en el entorno sin guardarlos en archivos. `medir.mjs` guarda únicamente resultados seleccionados: nunca la respuesta del login ni cabeceras de autorización. No activar HAR ni trazas de navegador con credenciales.

1. Frontend: `node node_modules/@angular/cli/bin/ng.js build --stats-json`. Guardar `dist/pharma-frontend/browser-stats.json`. Para el antes, sustituir temporalmente en `app.routes.ts` el `loadComponent` de MainLayout por su import y `component: MainLayout`. Restaurar después. Comparar compilaciones de producción con el mismo entorno.
2. En esbuild.github.io/analyze importar el metafile. Los cinco módulos iniciales se calculan sumando `bytesInOutput` de los outputs alcanzables desde main por imports estáticos. No sumar chunks dinámicos al Initial total. Las cifras de transferencia del CLI son estimaciones; los bytes de navegador son mediciones diferentes.
3. Iniciar Nginx y Redis con `docker compose -f deploy/docker-compose.yml up -d`. Arrancar el backend con perfil `prod`, Oracle de ensayo y Redis limpio en las claves de este ensayo. Reiniciar la JVM no elimina Redis: borrar solo las claves ensayadas antes de medir el primer fallo. Registrar contadores antes y después; usar deltas si hay otra actividad.
4. Desde backend: `node docs/s13/medir.mjs backend`. Hace 20 GET por caché, mide el primer fallo y 19 aciertos; guarda health y errores. Las métricas son locales a la JVM, no estadísticas globales de Redis. Para inspección manual: `/actuator/metrics/cache.gets?tag=name:categorias&tag=result:hit` con el token de administrador solo en memoria.
5. Ejecutar `node docs/s13/medir.mjs matriz`, luego `venta` y `baja`. C-04 registra desde la SPA, lee `X-Request-Id` y verifica stock 10 a 9. El primer ensayo C-05 mostró una baja lógica todavía visible. La corrección añade soloActivas al filtro y a la clave de caché; el listado habitual consulta activas en el servidor y Mostrar inactivas conserva la revisión administrativa. Repetir con c05-api y c05-spa. La API sin el filtro sigue devolviendo el historial para mantener compatibilidad.
6. Ejecutar `navegacion sin-precarga`. Cambiar temporalmente `app.config.ts` a `withPreloading(PreloadAllModules)`, reconstruir y ejecutar `navegacion con-precarga`. Restaurar y reconstruir. Cada variante usa 5 contextos limpios, caché deshabilitada, 1,5 Mbit/s, latencia de 80 ms y espera fija de 5 s después del login. No medir ambas a la vez. El tiempo login a Ventas incluye esa espera; reportar también clic a vista lista.
7. Ejecutar `cache antes`, cambiar un texto visible de Productos, reconstruir sin detener Nginx y ejecutar `cache despues`. El volumen actual de Docker sirve la compilación local. Para comparar sin vaciar la caché, usar un mismo contexto abierto durante el rebuild; consultar `B-despliegue.json`. Los orígenes de recarga se obtienen de Network del protocolo DevTools de Chrome, no se deducen solo del HTTP 200.
8. TTL: reiniciar backend con `CACHE_TTL=1m`, hacer GET a una clave no existente y consultar `docker compose -f deploy/docker-compose.yml exec -T redis redis-cli TTL '<clave>'`. Esperar más de 60 s y comprobar -2 sin otra lectura de la clave. Volver a arrancar con `CACHE_TTL=10m`, poblarla y verificar aproximadamente 600 s. No cambiar expiraciones de claves para simular el TTL de la aplicación.
9. Detener solo Redis; ejecutar `down` y probar la SPA. Health global debe ser DOWN y los productos responder 200 con fallback a Oracle. Volver a iniciar Redis y comprobar `up`. Durante una caída no se garantiza que una escritura invalide claves antiguas; purgarlas de forma selectiva antes de reconectar tráfico.
10. Buscar en `logs/pharma-backend.log` el ID de `D-venta-spa.json`. Usar `rg '<id>' logs/pharma-backend.log`. Auditar palabras y patrones JWT, secretos y DNI. No copiar coincidencias sin redacción al informe. Los archivos históricos no quedan saneados al corregir el código.

El backend se validó con `mvn -o package '-Dtest=!PharmaBackendApplicationTests'`: 42 pruebas, excluyendo la prueba de contexto dependiente del entorno. Frontend: `ng test --watch=false`: 53 pruebas. Las mediciones HTTP/SPA usan Oracle, Redis y Nginx reales.

## Entrega y versionamiento

Subir `Pacho_LP2_S13_Autonoma.pdf` al aula virtual y abrir PR de `feature/optimizacion-produccion-pacho` hacia `develop` en ambos repositorios. Revisar `git diff` para no incorporar otros trabajos locales ni secretos. El informe y las evidencias S13 están exceptuados del `.gitignore`; los documentos de otras sesiones siguen excluidos.

El requisito de tres días distintos solo se satisface con trabajo real en tres fechas. No usar fechas artificiales ni afirmar que un PR existe sin su enlace. Los cuerpos propuestos están en `solicitud-incorporacion.md`.

## Copia pública de las capturas

Las capturas `A-con-precarga.png`, `A-sin-precarga.png` y `B-recarga-ventas.png` ocultan la columna de clientes. Se conservan las fechas, el estado, los importes y las mediciones sin cambios. El manifiesto corresponde a estas copias.
