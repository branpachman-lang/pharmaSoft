# Cómo completar la actividad autónoma S10

Esta guía acompaña la [matriz](matriz-seguridad-s10.md), la colección `postman/PharmaSoft-S10-Seguridad.json` y el informe editable `Pacho_LP2_S10_Autonoma_Editable.docx`. El informe final y la matriz solo deben reflejar resultados realmente observados.

## Antes de comenzar

1. Inicia Oracle y PharmaBackend en el perfil `dev`. Comprueba `GET http://localhost:8080/api/health`.
2. Importa `postman/PharmaSoft-S10-Seguridad.json`. Si ya habías importado una versión anterior, elimínala y vuelve a importar este archivo: Postman no actualiza automáticamente una colección importada. En la pestaña **Variables** de la colección verifica `baseUrl = http://localhost:8080/api/v1` y, si Postman muestra columnas Initial y Current, coloca ese valor en ambas. En A-01 verás la URL `{{baseUrl}}/auth/login` en cada petición. Revisa las contraseñas **de prueba** y deja vacías las variables `token*` en el archivo del repositorio. Al ejecutar A-01, los scripts de Postman guardan los JWT localmente.
3. Ejecuta como ADMIN `GET /empleados`, `GET /usuarios` y `GET /roles`. Apunta el ID de un empleado que ya tenga usuario en `empleadoConUsuarioId`, el de uno libre en `empleadoLibreId`, tu ID ADMIN en `adminId` y un ID real de categoría en `categoriaId`. Si María Huamán ya tiene usuario, elige otro empleado libre y explica esa adaptación en U-02.
4. Crea `docs/evidencias_s10_autonoma/` si aún no existe. Guarda imágenes en PNG con el ID al comienzo. Para cada petición debe verse método, URL, código HTTP y cuerpo o mensaje; en errores de permisos muestra el encabezado `Authorization` **sin revelar el JWT completo**.

## Parte A

| Casos | Qué hacer | Captura necesaria |
|---|---|---|
| A-01 a A-04 | Ejecuta los logins en el orden de la colección. Compara el mensaje de A-02 y A-03; en A-04 documenta que la búsqueda de usuario ignora mayúsculas. | Una imagen por respuesta relevante; cuatro para A-01 o una composición legible. |
| T-01 y T-02 | T-01 envía el JWT sin `Bearer`. Para T-02 copia un JWT local, altera un carácter del segmento central y guarda la copia en `tokenAlterado`. | Petición y respuesta 401; oculta el token original. |
| T-03 | Copia un JWT válido a `tokenAnteriorSecreto`. Cambia temporalmente `app.jwt.secret` del perfil dev por otra clave válida, reinicia el backend y ejecuta T-03. Restaura el secreto al terminar. | Captura del 401 y, si ayuda, configuración temporal sin mostrar la clave. |
| T-04 | Cambia temporalmente `app.jwt.expiracion-minutos` a `1`, reinicia, inicia sesión, copia ese JWT a `tokenExpirable`, espera más de un minuto y ejecuta T-04. Restaura `60` y reinicia después. | Respuesta 401 con mensaje de expiración; anota hora de emisión y prueba. |
| T-05 y T-06 | T-05 imprime solo los claims en Postman Console. T-06 usa `Bearer` vacío. | Payload sin contraseña ni JWT completo; 401 de T-06. |
| P-01 a P-05 | Ejecuta los permisos por rol. P-01 y P-02 tienen varias solicitudes; captura cada una. P-04 son cuatro GET del ADMIN. | Código 403 o 200 y cuerpo correspondiente. |
| U-01 a U-03 | Primero verifica datos con `GET /empleados` y `/usuarios`. U-02 crea un usuario; puede ejecutarse solo una vez por empleado. Revisa `usuarios.password` y `usuario_roles` en SQL Developer. | Postman y SQL Developer para U-02; los demás, Postman. |
| C-01 | Desde `http://localhost:4200`, abre DevTools y ejecuta en Console un `fetch` autenticado a `/api/v1/auth/me` con un JWT de prueba. En Network observa `OPTIONS` y `GET`. | Una o dos capturas de Network con estado de ambas solicitudes y sin JWT visible. |

Para C-01, la llamada debe originarse desde la página de la SPA; Postman no aplica la política CORS del navegador. Si el navegador no muestra `OPTIONS`, activa “Preserve log”, recarga la página y repite la llamada. Al copiar el token a Console, no lo incluyas en la captura.

Ejemplo para la consola de Chrome con un token **local de clase** (sustituye solo el texto entre comillas):

```javascript
const tokenS10 = 'PEGA_AQUI_EL_JWT_DE_PRUEBA';
fetch('http://localhost:8080/api/v1/auth/me', {
  headers: { Authorization: `Bearer ${tokenS10}` }
}).then(r => console.log('Estado GET:', r.status));
```

Para el control SQL de U-02, puedes consultar el usuario creado y sus roles con:

```sql
SELECT u.id, u.username, u.password AS hash_bcrypt, r.nombre AS rol
FROM usuarios u
JOIN usuario_roles ur ON ur.usuario_id = u.id
JOIN roles r ON r.id = ur.rol_id
WHERE u.username = 's10_nuevo';
```

Si cambiaste `usuarioPruebaUsername` en Postman, cambia también el valor del `WHERE`. La captura debe mostrar que el hash empieza por `$2a$10$` y que existe una fila en `usuario_roles`, sin exponer contraseñas en texto plano.

## Parte B

| Casos | Qué hacer | Captura necesaria |
|---|---|---|
| B-01 a B-04 | Con token de vendedor, ejecuta el cambio válido y luego los tres errores. B-01 actualiza la contraseña local de la colección y hace login con la nueva. Si ya habías cambiado la clave, ajusta `vendedorPassword` antes de empezar. | 204 y nuevo login 200; 409, 409 y 400 con sus mensajes. |
| B-05 | Usa el usuario creado en U-02 o prepara otro usuario de prueba. Inicia sesión para conservar su token; prueba POST categoría antes del cambio (403), asigna roles 2 y 3, repite con el **mismo token** (201). | Antes 403, asignación 200, después 201 y roles nuevos en `/auth/me`. |
| B-06 | Prueba conjunto vacío, rol inexistente y usuario inexistente. | 400, 404 y 404. |
| B-07 | Desactiva el usuario de prueba; sin renovar su token consulta `/auth/me` y luego intenta login. | 200 con `estado:false`, 401 del token anterior y 401 genérico del login. |
| B-08 | Como ADMIN intenta quitarte el rol ADMIN y desactivar tu propia cuenta. | Dos respuestas 409. |

## Completar y entregar

1. Copia las capturas a `docs/evidencias_s10_autonoma/` y avísame. Revisaré que coincidan con los IDs y completaré **Resultado obtenido**, **Estado** y vínculos de la matriz.
2. Completaré el recuento C1 y las fichas C2 del informe editable a partir de la evidencia. C3 ya contiene un borrador fundamentado en el código; lo revisaré con los resultados. Convertiré el documento a `docs/informe-s10.pdf` y a `Pacho_LP2_S10_Autonoma.pdf` para el aula virtual.
3. La consigna exige tres commits en **días distintos**. No se deben fingir fechas. Guarda los cambios pendientes de cada jornada y realiza los commits en fechas reales antes del 21 de octubre a las 23:59. La solicitud de incorporación hacia `master` se prepara cuando el informe y las capturas estén completos.

Los cambios de contraseña, creación, roles y estado modifican Oracle. Usa cuentas de prueba y no reutilices una cuenta que necesites para otros casos.
