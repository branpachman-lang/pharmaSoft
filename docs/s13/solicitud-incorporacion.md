Título: feat(observabilidad): completar trazabilidad y evaluación de producción S13

Destino: develop. Origen: feature/optimizacion-produccion-pacho.

Los errores de negocio, validación, autenticación y fallos inesperados devuelven el requestId de la petición, que permite correlacionar lo que ve la SPA con el log. Se elimina el DNI del log de registro de clientes y se añaden eventos de venta sin datos personales. CACHE_TTL permite repetir el ensayo de expiración sin editar valores de producción.

Incluye informe S13, mediciones y capturas sin credenciales, procedimiento de reproducción y guía de despliegue para tres locales. C-05 incorpora el filtro paginado soloActivas: la categoría desaparece de la vista habitual y se puede consultar con Mostrar inactivas. Se preserva la baja lógica y la consulta API por defecto.

Validación de la ronda final. Pasaron las 43 pruebas del backend, incluido el arranque con Oracle y Redis locales. También se verificaron las peticiones HTTP y la venta de ensayo con Nginx. Revisar los pendientes del informe antes de producción.
