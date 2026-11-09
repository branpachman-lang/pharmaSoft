# Lista de capturas de la actividad autónoma S13

La [guía paso a paso](Guia_S13_Autonoma_Paso_a_Paso.pdf) describe cómo repetir cada prueba. Este inventario distingue lo que quedó guardado de los nombres sugeridos para una nueva ejecución. Las capturas compartidas se reutilizan sin repetir la venta.

## Evidencias guardadas

Los archivos con prefijo `AA-` están en la [ronda de Edge y servicios locales](evidencias-s13-autonoma-manual/2026-11-08-control-pc/). Los archivos de la primera ronda están en [evidencias-s13](evidencias-s13/).

| Prueba | Captura o registro verificado |
| --- | --- |
| Preparación | `AA-00-02-health-inicial.png` en Postman y `H01-login-correcto-despues.jpg` en Edge |
| A01 | `AA-A01-03` a `AA-A01-08` muestran el analizador y los módulos. `A01-browser-stats-final.json` conserva el archivo analizado |
| A02 | `A02-build-antes.txt` y `A02-build-despues.txt` conservan las salidas reales del compilador y se acompañan de los dos metafiles |
| A03 | `A-sin-precarga.png`, `A-con-precarga.png` y los JSON de las cinco corridas de cada variante |
| B01–B02 | `B-cabeceras.png`, `B-recarga-ventas.png`, `B-recarga.json` y `B01-cabeceras-curl.json` |
| B03 | `B-productos-antes.png`, `B-productos-despues.png`, `B-build-despliegue.txt` y `B-despliegue.json` |
| C01–C02 | `C01-C02-series-20.json` registra las 40 consultas, tiempos y contadores. `C-aciertos.png` resume la primera ronda |
| C03 | `C03-ttl-inicial.json`, `C03-ttl-expirada.json` y `C03-ttl-restaurada.json` |
| C04–C06 | Capturas Edge `AA-C04-*`, `AA-C05-*`, `AA-C06-*` y comprobaciones API en `C-matriz-api.json` |
| C07 | `AA-C07-*` muestra stock inicial, revisión, comprobante y stock final. La cabecera 201 de la primera venta está en `D-venta-spa.json` |
| C08 | `AA-C08-*` muestra la categoría activa, la baja y su consulta en el historial |
| C09 | `C-06-redis-detenido.png`, `C09-health-off.json`, `C09-health-on-transicion.json` y `C09-health-on.json` |
| D01 | `D-venta-log.png`, `D-venta-spa.json` y `D-venta-traza.txt` de la primera venta. `D01-identificadores.json` y `D01-traza-venta.txt` de la venta de Edge |
| D02 | `AA-D02-03-error-spa.jpg`, `D02-error-spa.json` y `D02-errores-api.json` con cabecera y cuerpo de 400, 401, 404 y 409 |
| D03 | `D03-auditoria.json` y `D03-clave-jwt.json` conservan conteos de la auditoría |
| D04 | `AA-00-02-health-inicial.png`, los JSON de salud de C09 y `D04-metricas-ventas.json` |
| E01 | Secciones «Despliegue en producción» en ambos README |
| F01 | La [verificación de la rama de entrega](evidencias-s13-autonoma-manual/2026-11-08-parte-f/) conserva el antes y el después, con 45 pruebas de frontend y 43 de backend aprobadas. `F01-http-nginx.json` registra la verificación HTTP. La ronda del directorio de trabajo conserva sus 53 pruebas frontend en `F-pruebas-ronda.json` |
| F02 | `F02-historial-PharmaBackend.txt`, `F02-historial-pharma-frontend.txt` y `F-resumen.json` registran fechas y ramas remotas. Los textos de PR están preparados. Faltan fechas reales, publicación de PR y carga al aula |

## Nombres propuestos para repetir las capturas

Se pueden usar las evidencias anteriores al sustentar. Las casillas de esta sección sirven para registrar una nueva ejecución manual.


## Preparación

- [ ] AA-00-01-servicios.png
- [ ] AA-00-02-health-inicial.png

## A01 Analizador y cinco módulos iniciales

- [ ] AA-A01-01-build-initial.png
- [ ] AA-A01-02-build-lazy.png
- [ ] AA-A01-03-analyzer-general.png
- [ ] AA-A01-04-modulos-iniciales.png

## A02 Mejora adicional y tamaño antes y después

- [ ] AA-A02-01-antes.png
- [ ] AA-A02-02-cambio-layout.png
- [ ] AA-A02-03-despues.png

## A03 Navegación con y sin precarga

- [ ] AA-A03-01-sin-config.png
- [ ] AA-A03-02-sin-red.png
- [ ] AA-A03-03-sin-tiempos.png
- [ ] AA-A03-04-con-config.png
- [ ] AA-A03-05-con-red.png
- [ ] AA-A03-06-con-tiempos.png
- [ ] AA-A03-07-restauracion.png

## B01 Encabezados de los cinco recursos

- [ ] AA-B01-01-curl-estaticos.png
- [ ] AA-B01-02-curl-api.png
- [ ] AA-B01-03-index.png
- [ ] AA-B01-04-main.png
- [ ] AA-B01-05-ventas.png
- [ ] AA-B01-06-styles.png
- [ ] AA-B01-07-api.png

## B02 Origen de los recursos en una recarga normal

- [ ] AA-B02-01-primera-carga.png
- [ ] AA-B02-02-f5-ventas.png
- [ ] AA-B02-03-f5-categorias.png
- [ ] AA-B02-04-documento.png

## B03 Despliegue sin detener Nginx

- [ ] AA-B03-01-antes.png
- [ ] AA-B03-02-build.png
- [ ] AA-B03-03-despues.png
- [ ] AA-B03-04-archivos.png
- [ ] AA-B03-05-nginx.png

## C01 Veinte consultas de categorías y tasa de aciertos

- [ ] AA-C01-01-clave-ausente.png
- [ ] AA-C01-02-contadores-antes.png
- [ ] AA-C01-03-primer-get.png
- [ ] AA-C01-04-runner-19.png
- [ ] AA-C01-05-contadores-despues.png

## C02 Veinte consultas de productos y tasa de aciertos

- [ ] AA-C02-01-clave-ausente.png
- [ ] AA-C02-02-contadores-antes.png
- [ ] AA-C02-03-primer-get.png
- [ ] AA-C02-04-runner-19.png
- [ ] AA-C02-05-contadores-despues.png

## C03 Vigencia de un minuto y restauración a diez

- [ ] AA-C03-01-config-1m.png
- [ ] AA-C03-02-ttl-inicial.png
- [ ] AA-C03-03-expirada.png
- [ ] AA-C03-04-config-10m.png
- [ ] AA-C03-05-ttl-restaurado.png

## C04 Crear una categoría con la lista previamente cacheada

- [ ] AA-C04-01-lista-antes.png
- [ ] AA-C04-02-creacion.png
- [ ] AA-C04-03-lista-despues.png

## C05 Renombrar una categoría y comprobar sus productos

- [ ] AA-C05-01-producto-antes.png
- [ ] AA-C05-02-renombrado.png
- [ ] AA-C05-03-producto-despues.png

## C06 Editar un precio y comprobar detalle y lista

- [ ] AA-C06-01-detalle-antes.png
- [ ] AA-C06-02-lista-antes.png
- [ ] AA-C06-03-edicion.png
- [ ] AA-C06-04-detalle-despues.png
- [ ] AA-C06-05-lista-despues.png

## C07 Venta desde la SPA y descuento de stock

- [ ] AA-C07-01-stock-antes.png
- [ ] AA-C07-02-revision-venta.png
- [ ] AA-C07-03-venta-201.png
- [ ] AA-C07-04-stock-despues.png
- [ ] AA-D01-01-request-id.png

## C08 Baja de categoría vacía y consulta de inactivas

- [ ] AA-C08-01-activa-antes.png
- [ ] AA-C08-02-baja.png
- [ ] AA-C08-03-activa-despues.png
- [ ] AA-C08-04-inactivas.png

## C09 Redis detenido y cuatro respuestas de health

- [ ] AA-C09-01-health-up-publico.png
- [ ] AA-C09-02-health-up-admin.png
- [ ] AA-C09-03-redis-parado.png
- [ ] AA-C09-04-productos-200.png
- [ ] AA-C09-05-health-down-publico.png
- [ ] AA-C09-06-health-down-admin.png
- [ ] AA-C09-07-warn.png
- [ ] AA-C09-08-restaurado.png

## D01 Reconstruir la venta en el log

- [ ] AA-D01-02-log-venta.png

## D02 Código de seguimiento en el backend y en la SPA

- [ ] AA-D02-01-error-cuerpo.png
- [ ] AA-D02-02-error-cabecera.png
- [ ] AA-D02-03-error-spa.png
- [ ] AA-D02-04-log.png
- [ ] AA-D02-05-401.png
- [ ] AA-D02-06-400.png
- [ ] AA-D02-07-409.png

## D03 Auditoría de secretos en el log de producción

- [ ] AA-D03-01-archivo-y-conteos.png
- [ ] AA-D03-02-patrones.png
- [ ] AA-D03-03-correccion.png
- [ ] AA-D03-04-repeticion.png

## D04 Métricas HTTP de ventas

- [ ] AA-D04-01-uri-ventas.png
- [ ] AA-D04-02-post-ventas.png

## E01 Revisión del despliegue y de los dos README

- [ ] AA-E01-01-readme-backend.png
- [ ] AA-E01-02-readme-frontend.png
- [ ] AA-E01-03-arquitectura.png

## F01 Pruebas automatizadas como complemento

- [ ] AA-F01-01-tests-frontend.png
- [ ] AA-F01-02-tests-backend.png

## F02 Versionamiento y entrega

- [ ] AA-F02-01-historial-backend.png
- [ ] AA-F02-02-historial-frontend.png
- [ ] AA-F02-03-pr-backend.png
- [ ] AA-F02-04-pr-frontend.png
- [ ] AA-F02-05-aula.png

En A03 conserva además las cinco repeticiones de cada variante. Añade sufijos de corrida a sus capturas.
