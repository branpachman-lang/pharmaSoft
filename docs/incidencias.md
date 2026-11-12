# Incidencias de la práctica de la sesión 14

| ID | Módulo | Reproducción y resultado inicial | Severidad | Causa | Corrección | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| INC-01 | Nginx y autenticación | Abrir la SPA en un puerto de laboratorio y enviar el formulario de login. Chrome recibió HTTP 403 y seis casos no pudieron completar la primera corrida. | Alta | Nginx reenviaba el host sin el puerto original. Spring interpretó el origen del navegador como distinto. | Nginx conserva el host y puerto con `$http_host`. El backend de laboratorio recibió el origen exacto en la configuración de CORS. Frontend `e9e768c`. | Cerrada |
| INC-02 | Prueba del comprobante | Confirmar la venta. La API devolvió HTTP 201 y la SPA abrió el comprobante con `?nueva=1`. La segunda corrida obtuvo 6 de 7. | Media | El criterio de URL de Playwright esperaba que la URL terminara en el ID. | La prueba verifica la ruta y el parámetro `nueva` del comprobante. Frontend `1c73f32`. | Cerrada |
| INC-03 | Prueba de caché del backend | Ejecutar las pruebas aisladas de Maven. La comprobación de invalidación al renombrar una categoría obtuvo una referencia nula. | Media | El doble de prueba todavía simulaba `save`. La actualización usa `saveAndFlush` para devolver los campos de auditoría ya actualizados. | Se ajustó la simulación al método de persistencia. Backend `242f390`. | Cerrada |

La corrida final de Playwright aprobó 7 de 7 casos en cada repetición, con cero reintentos. La suite aislada de Maven aprobó 42 de 42. Las pruebas se ejecutaron en el esquema Oracle de ensayo `PHARMA_S14`.
