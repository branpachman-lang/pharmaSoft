# Línea base de la sesión 14

El 12 de noviembre de 2026 se midió el paso 2 en el esquema Oracle local `PHARMA_S14`. Se creó la estructura a partir del backend de S13. Como las ramas base carecen de la cadena V1–V3, Flyway registró la versión 3 como línea base en el esquema dedicado y aplicó la migración SQL V4. Se verificaron 5 000 productos y 20 000 ventas sintéticas. Las ventas sintéticas carecen de detalle y sirven para medir el listado.

La medición hizo una petición por fila a la API de S14, con la caché desactivada. Los tiempos incluyen el transporte HTTP local. La [evidencia JSON](linea-base-s14.json) conserva las respuestas resumidas y las sentencias de Hibernate, que muestran `OFFSET … FETCH` y `COUNT` en ambos listados.

| Petición | HTTP | Filas | Total | Bytes | Tiempo |
| --- | ---: | ---: | ---: | ---: | ---: |
| Productos, página 0, tamaño 20 | 200 | 20 | 5 000 | 5 450 | 111,26 ms |
| Productos, página 0, tamaño 100 | 200 | 100 | 5 000 | 26 884 | 42,06 ms |
| Productos, página 249, tamaño 20 | 200 | 20 | 5 000 | 5 498 | 32,81 ms |
| Productos, página 0, tamaño 500 | 409 | — | — | 237 | 21,77 ms |
| Ventas del 1 al 12 de noviembre, página 0 | 200 | 10 | 637 | 1 892 | 84,07 ms |

La página 249 devolvió `ultima=true`. En la versión S13 la lista de Productos ya tenía controles y filtraba la categoría dentro de la página descargada. S14 aplica ese filtro antes de paginar y guarda la selección en la URL.

Para repetir la carga, usa SQL*Plus con la cuenta del esquema `PHARMA_S14`, después de aplicar V4 y crear una categoría y un cliente sintéticos. Ejecuta `@docs/sql/volumen_pruebas.sql` desde la raíz del backend. El script conserva las filas de carga existentes si se ejecuta de nuevo. Para la medición, ejecuta la API en ese esquema con `SPRING_CACHE_TYPE=none` y SQL de Hibernate visible. Las operaciones sobre ventas y los reportes de los pasos siguientes requieren sus propios datos de prueba.
