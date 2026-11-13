# Guía de pruebas de la práctica S14

Trabaja en `PharmaBackend` y `pharma-frontend`, en la rama `feature/integracion-estabilizacion-pacho`. Guarda las capturas de **tu ejecución** en `PharmaBackend/docs/s14/capturas`. Usa los nombres de archivo indicados y registra la fecha, el resultado y el identificador de seguimiento cuando corresponda. Las mediciones y resultados ya obtenidos sirven de referencia para comparar.

Consulta el [informe final](../Pacho_LP2_S14_Practica.pdf), las [figuras publicadas](../evidencias-s14/practica-final/) y el [resultado final de Playwright](P03-resultado-final.json). Las figuras publicadas corresponden al informe y tienen ocultos los tokens y los números de documento que aparecían en pantalla.

## Preparar el entorno

1. Abre Docker Desktop y confirma que `oracle-local` esté iniciado. El esquema `PHARMA_S14` ya tiene la migración V4 y los datos sintéticos de volumen.
2. Abre una terminal de **Windows PowerShell 5.1 o PowerShell 7** en el proyecto original `PharmaBackend`. Ejecuta:

   ```powershell
   .\docs\s14\Iniciar-Laboratorio-S14.ps1
   ```

3. Elige una clave temporal cuando el lanzador te la pida. Úsala para los usuarios `admin_s14`, `vendedor_s14` y `almacen_s14`. La terminal debe quedar abierta. Espera **backend UP · Redis PONG · SPA HTTP 200** y abre `http://127.0.0.1:18085` en Chrome o Edge. Captura la terminal como `P00-entorno.png`.
4. Para reconstruir tras editar el código, ejecuta `npm.cmd run build` en el frontend y `.\mvnw.cmd clean package -DskipTests` con Java 21 en el backend. Detén el laboratorio antes de volver a compilar el JAR.
5. En Postman pulsa **Import** y selecciona la [colección de la práctica](postman/PharmaSoft-S14-Practica.postman_collection.json) y el [entorno local](postman/PharmaSoft-S14-Local.postman_environment.json). Selecciona **PharmaSoft S14 - Laboratorio local** y escribe la clave temporal del lanzador en el valor local de `clave_s14`. En **00 Entorno y sesión**, ejecuta **Backend UP**, **Login ADMIN** y **Login VENDEDOR**. Los dos logins guardan automáticamente su token en el entorno. Repite ambos al reiniciar el laboratorio o al vencer la sesión. Para las capturas, oculta los tokens y muestra únicamente los encabezados de respuesta necesarios.

Si al pulsar **Send** en **Login ADMIN** el panel de respuesta queda vacío, verifica el entorno activo y el valor local de `clave_s14`. El script omite el envío cuando falta esa variable. Conserva `{{clave_json}}` en el cuerpo. El script la prepara con la clave del entorno. La URL de la solicitud es `{{base}}/api/v1/auth/login`.

Ejecuta las solicitudes según avances por la guía. Las carpetas de venta y precio tienen consultas que dependen de acciones hechas en la SPA.

| Cuándo | Variables que debes completar |
| --- | --- |
| Antes de I-03 | `producto_id` del producto activo de ensayo. Haz la primera consulta de stock antes de confirmar la venta. |
| Después de I-03 | `venta_id` del comprobante y `venta_request_id` del encabezado `X-Request-Id` de la respuesta **201** del POST de venta. |
| Antes del rollback de I-05 | `cliente_id` del cliente usado en la venta y `producto_agotado_id` del segundo producto de ensayo. Ejecuta en orden las seis solicitudes de **04 I05 Rollback con producto agotado**. |
| Después de editar el precio en I-06 | `precio_request_id` del encabezado `X-Request-Id` de la respuesta del PUT de Productos. `precio_nuevo` ya contiene `15`. |

## P01 Medición de la línea base

1. Ejecuta en orden las seis solicitudes de **01 P01 Mediciones de paginación**. Anota el estado, el tiempo y el tamaño que muestra Postman. El total puede haber aumentado por los datos de pruebas anteriores. La primera consulta guarda `totalPaginas - 1` para que P01-03 pida la última página actual.

   | Solicitud | Qué debes comprobar | Captura |
   | --- | --- | --- |
   | `/api/v1/productos?pagina=0&tamanio=20` | HTTP 200, máximo 20 filas, total mayor que el tamaño | `P01-01-productos-20.png` |
   | `/api/v1/productos?pagina=0&tamanio=100` | HTTP 200, 100 filas en la primera página | `P01-02-productos-100.png` |
   | `/api/v1/productos?pagina=249&tamanio=20` | La guía usa 249 para 5 000 productos. Repite con la última página actual y verifica `ultima: true` | `P01-03-ultima-pagina.png` |
   | `/api/v1/productos?pagina=0&tamanio=500` | HTTP 409 y mensaje de tamaño permitido | `P01-04-limite-409.png` |
   | `/api/v1/ventas/buscar?desde=2026-11-01&hasta=2026-11-12&pagina=0` | HTTP 200, lista de la primera página y total del rango | `P01-05-ventas-filtradas.png` |
   | `/api/v1/productos?pagina=0&tamanio=20&ordenarPor=categoriaNombre` | HTTP 409 por campo de orden fuera de la lista permitida | `P01-06-orden-no-permitido.png` |

2. En otra terminal de PowerShell, ejecuta los conteos sobre el contenedor Oracle local. Las ventas creadas para la matriz tienen un autor distinto y se cuentan aparte. Captura los resultados como `P01-07-conteos.png`. El registro de la medición anterior conserva las sentencias de Hibernate con `OFFSET … FETCH` y `COUNT` en `docs/sql/linea-base-s14.json`.

   ```powershell
   @'
   alter session set container=FREEPDB1;
   select count(*) productos_carga from PHARMA_S14.productos where creado_por = 's14-volumen';
   select count(*) ventas_carga from PHARMA_S14.ventas where creado_por = 's14-volumen';
   exit
   '@ | docker exec -i oracle-local sqlplus -s / as sysdba
   ```

## P02 Paginación de Productos en la SPA

1. Inicia sesión como `admin_s14`. Abre **Productos** y luego **F12 → Red → Fetch/XHR**. Limpia la lista de Red.
2. Pulsa **Página siguiente**. Verifica que la URL tenga `pagina=1`, el paginador diga **Página 2** y el GET de productos incluya `pagina=1` con HTTP 200. Captura la vista y la pestaña Red en `P02-01-segunda-pagina.png`.
3. Pulsa **F5**. Confirma que permanece la página 2. Captura `P02-02-recarga.png`.
4. Cambia **Filas por página** de 20 a 50. Comprueba que vuelve a la primera página y la URL muestra `tamanio=50`. Ordena por **Precio** y revisa `orden=precio` y `dir`. Captura `P02-03-tamanio-orden.png`.

## Preparar registros para la matriz de integración

1. Como administrador crea una categoría con un nombre único, por ejemplo **S14 Aula 0915**.
2. En esa categoría crea tres productos con nombres que comiencen igual, por ejemplo **S14 Aula 0915 activo**, **S14 Aula 0915 inactivo** y **S14 Aula 0915 agotado**. Usa precio **S/ 12,50** para los tres. Configura el primero activo con stock **10**, el segundo inactivo con stock **10** y el tercero activo con stock **0**.
3. Aplica el filtro de categoría en Productos y captura los tres registros en `M00-catalogo-inicial.png`. Anota el ID del producto activo. Si la interfaz de alta no permite escoger inactivo, créalo y usa **Dar de baja**.
4. Abre una sesión separada para el vendedor, por ejemplo una ventana de incógnito. Conserva la del administrador para Productos y Postman. Verifica que la primera sesión indique ADMIN y la otra VENDEDOR.

## Matriz manual del paso 8

### I-01 Cliente nuevo en el buscador de Ventas

1. Como vendedor abre **Clientes → Nuevo cliente**. Registra un cliente de prueba con un apellido único, correo terminado en `@example.invalid` y un DNI ficticio que no esté ocupado.
2. Abre **Ventas → Nueva venta** y escribe el apellido en **Buscar cliente activo**. Comprueba que aparece y selecciónalo. Captura el resultado como `I01-cliente-en-venta.png`. Recorta el DNI si aparece.

### I-02 Solo productos activos con stock

1. En la misma venta busca el prefijo común de los tres productos. Debe salir únicamente el activo con stock, con precio **S/ 12,50** y **Stock 10**.
2. Captura la lista como `I02-producto-ofrecido.png`, selecciona el producto y cambia la cantidad a **2**. Comprueba que el total es **S/ 25,00**.

### I-03 Venta confirmada y stock actualizado

1. Abre **Red** en DevTools y activa **Conservar registro**. Pulsa **Revisar venta**, desmarca la impresión automática y pulsa **Confirmar venta**.
2. Anota el ID que aparece en la URL del comprobante y el estado **201** del POST `/api/v1/ventas`. En **Encabezados de respuesta**, anota `X-Request-Id`. Captura la respuesta y el comprobante como `I03-01-venta-201.png` e `I03-02-comprobante.png`. Excluye los encabezados de solicitud y los datos personales.
3. Desde el menú abre **Productos** y vuelve a seleccionar la categoría de ensayo. El producto activo debe mostrar **8 unidades** con navegación normal. Captura `I03-03-stock-despues.png`.

### I-04 Venta visible en Reportes

1. Como administrador abre **Inicio** y baja hasta **Productos más vendidos**, o consulta `GET /api/v1/reportes/productos-mas-vendidos` en Postman con ADMIN.
2. Busca el producto por su nombre o ID. Para un producto recién creado y vendido una sola vez, verifica **2 unidades** y **S/ 25,00**. Captura `I04-reporte.png`.

### I-05 Venta registrada en la bitácora

1. Con ADMIN, envía `GET /api/v1/auditoria?accion=VENTA_REGISTRADA&pagina=0&tamanio=20` en Postman. Busca el evento con el ID de venta de I-03.
2. Verifica `usuario: vendedor_s14`, `entidadId` igual al ID de la venta y el mismo `requestId` que anotaste en DevTools. Captura `I05-01-evento-venta.png`.
3. Repite la consulta con el token de vendedor. Debe responder **403**. Captura `I05-02-vendedor-403.png`.
4. Para comprobar el rollback, registra primero el stock y el total de eventos `VENTA_REGISTRADA`. Con el token de vendedor, envía un POST a `/api/v1/ventas` con el mismo cliente y dos líneas: una unidad del producto activo y una del agotado. El cuerpo usa `clienteId` y `detalles`, con `productoId` y `cantidad` en cada línea. Debe devolver **409**. Repite las dos lecturas. El stock y el total de eventos deben conservar los valores anteriores. Captura `I05-03-rollback.png`.

### I-06 Edición de precio y autor

1. Como administrador, abre **Productos → Editar** en la fila del producto activo. Cambia el precio de **S/ 12,50** a **S/ 15,00** y guarda. Anota el identificador de la respuesta PUT en DevTools.
2. Reabre la edición. Debe mostrarse **Modificado por admin_s14**. Captura `I06-01-autor.png`.
3. Con ADMIN, envía `GET /api/v1/auditoria?accion=PRECIO_MODIFICADO&pagina=0&tamanio=20`. Ubica el ID del producto y verifica el valor anterior, el nuevo, el usuario y el `requestId`. Captura `I06-02-evento-precio.png`.

### I-07 Expiración durante una venta

1. Haz este caso al final de las pruebas manuales. Detén el laboratorio pulsando Enter en su terminal y vuelve a iniciarlo con `.\docs\s14\Iniciar-Laboratorio-S14.ps1 -ExpiracionMinutos 1`.
2. En una sesión nueva, entra como vendedor, abre **Nueva venta** y escribe una búsqueda o selecciona el cliente. Espera el vencimiento sin confirmar la venta.
3. Comprueba que la SPA vuelve al login con `expirada=1` y `returnUrl` hacia `/ventas/nueva`. Captura `I07-01-login-expirado.png`.
4. Ingresa otra vez. Comprueba que regresa a **Nueva venta**. Captura `I07-02-retorno.png`. Registra si recuperó los datos del borrador por separado de la comprobación de ruta.
5. Reinicia con la duración normal antes de ejecutar Playwright.

### I-08 Cambiar filtros desde la página 5 de Ventas

1. Con una sesión válida, abre `http://127.0.0.1:18085/ventas?pagina=4`. Debe aparecer **Página 5**. Captura `I08-01-pagina-5.png`.
2. Elige **Desde 01/11/2026** y **Hasta 12/11/2026**. Pulsa **Buscar**.
3. Verifica **Página 1**, `pagina=0` y ambas fechas en la URL. Captura `I08-02-filtros-pagina-1.png`.

## P03 Playwright y evidencias del paso 9

Si quieres observar autenticación y permisos antes de correr Playwright, usa sesiones separadas:

1. En una ventana privada, abre `/ventas`. Revisa que la URL pase a `/login?returnUrl=%2Fventas`. Ingresa como vendedor y comprueba que vuelves a Ventas. Guarda `P03-A01-retorno-login.png`.
2. En otra sesión sin autenticar, intenta entrar con un usuario inexistente de nombre único. Comprueba el mensaje de credenciales incorrectas y el HTTP 401 de `/auth/login`. Con ADMIN, filtra `/api/v1/auditoria?accion=LOGIN_FALLIDO&usuario=<usuario-del-intento>`. Compara el `requestId` del evento con la respuesta 401. Guarda `P03-A02-login-fallido.png`.
3. Ingresa como almacenero. Confirma que el menú no muestra Ventas. Abre `/ventas` desde la barra y verifica **Acceso denegado**. Guarda `P03-A03-almacen.png`.
4. Ingresa como vendedor y abre Productos. Confirma que ves las filas, pero no **Nuevo producto** ni **Editar**. Guarda `P03-A04-vendedor.png`. La verificación manual de vencimiento está en I-07 y los casos de paginación y venta están en P02 e I-01 a I-08.

En otra terminal PowerShell, en el proyecto original `pharma-frontend`, prepara la ejecución mientras el laboratorio siga abierto:

```powershell
$env:S14_BASE_URL = 'http://127.0.0.1:18085'
$env:S14_BROWSER_CHANNEL = 'chrome'
$clave = Read-Host 'Clave temporal de los usuarios S14' -AsSecureString
$env:S14_LAB_LOGIN = [System.Net.NetworkCredential]::new('', $clave).Password
$clave.Dispose()
npx.cmd playwright test --ui
```

En modo visual puedes lanzar los siete casos individualmente. Anota el primer resultado y abre el detalle si falla:

| N.º | Archivo | Qué comprueba el caso |
| --- | --- | --- |
| 1 | `autenticacion.spec.ts` | Ruta protegida sin sesión y parámetro `returnUrl` |
| 2 | `autenticacion.spec.ts` | Credenciales incorrectas, HTTP 401 y evento LOGIN_FALLIDO |
| 3 | `autenticacion.spec.ts` | Retorno a Ventas y regreso a Nueva venta tras adelantar el reloj del navegador |
| 4 | `permisos.spec.ts` | Almacenero sin menú Ventas y acceso directo denegado |
| 5 | `permisos.spec.ts` | Vendedor consulta Productos sin editar |
| 6 | `paginacion.spec.ts` | Segunda página de Productos tras F5 y vuelta a página 1 al filtrar Ventas |
| 7 | `flujo-venta.spec.ts` | Venta con stock, reporte, auditoría, precio y rollback |

Cierra el modo visual antes de la corrida formal. Ejecuta:

```powershell
npx.cmd playwright test --repeat-each=3
npx.cmd playwright show-report
```

1. Captura la consola como `P03-01-playwright-consola.png`. Se esperan **21 aprobadas** si pasan las siete en cada repetición. El resumen JSON queda en `test-results/resumen.json`.
2. Captura la pantalla general del reporte HTML como `P03-02-playwright-html.png`. En el caso de venta, abre el adjunto **Stock después de la venta**. Si un caso falla, guarda el detalle antes de repetir.
3. En **Red** o en el registro de acceso que muestra el lanzador, verifica si hubo HTTP 500. Anota los errores de consola del flujo de venta. Las respuestas esperadas 401, 403 y 409 se documentan con sus casos.
4. Cuando termines, elimina la variable de la terminal con `Remove-Item Env:S14_LAB_LOGIN`. Pulsa Enter en la terminal del lanzador para detener el laboratorio.

## P04 Registrar incidencias y completar el informe

1. Si algo falla, anota primero el ID, módulo, pasos, severidad y resultado observado en `docs/incidencias.md`. Después registra la causa, la corrección y el commit correspondiente. Repite el caso y vuelve a ejecutar la suite completa.
2. En el informe editable sustituye los campos entre corchetes con tus resultados. Inserta las capturas junto al caso que respaldan. La tabla de evidencias de la guía exige conteos, tiempos y bytes, el HTTP 409, los ocho casos de integración, los eventos de auditoría y las tres corridas de Playwright.
3. Guarda la versión final como **Pacho_LP2_S14_Practica.pdf**. Comprueba que las capturas se lean y que el total coincida con tu consola y el HTML.
