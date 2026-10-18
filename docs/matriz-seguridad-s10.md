# Matriz de pruebas de seguridad — Sesión 10

**Estudiante:** Pacho<br>
**Rama:** `feature/seguridad-pruebas-pacho`<br>
**Entorno:** `http://localhost:8080/api/v1`<br>
**Estado:** pendiente de ejecución y capturas. No se consignan resultados supuestos.

Registra en **Resultado obtenido** el código HTTP y el mensaje o dato observado. Cambia **Pendiente** por **Pasa** o **Falla** solo después de ejecutar el caso. Copia las imágenes a `docs/evidencias_s10_autonoma/` con el ID al inicio del nombre (por ejemplo, `T-02_postman.png`). Para un caso con varias peticiones usa sufijos `_1`, `_2`, etc. Después se insertarán aquí y en el informe final las capturas pertinentes. Oculta los JWT y las contraseñas visibles antes de compartir las imágenes.

| ID | Grupo | Usuario / token | Petición o comprobación | Resultado esperado (código y mensaje) | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|---|
| A-01 | Autenticación | Admin, vendedor, almacenero, supervisor | POST `/auth/login` con cada cuenta | 200; roles y permisos de cada cuenta. Supervisor reúne los permisos de VENDEDOR y ALMACENERO. | Pendiente | Pendiente | `A-01_*.png` |
| A-02 | Autenticación | Inexistente y contraseña errónea | Dos POST `/auth/login` | 401 y mensaje idéntico: «Usuario o contraseña incorrectos». | Pendiente | Pendiente | `A-02_*.png` |
| A-03 | Autenticación | Cuenta inactiva | POST `/auth/login` | 401; mensaje genérico, sin revelar existencia de la cuenta. | Pendiente | Pendiente | `A-03_postman.png` |
| A-04 | Autenticación | `VENDEDOR` en mayúsculas | POST `/auth/login` | 200 según `findByUsernameIgnoreCase`; justificar esta regla. | Pendiente | Pendiente | `A-04_postman.png` |
| T-01 | Token | Token válido sin prefijo | GET `/auth/me`, `Authorization: <token>` | 401; «Debe iniciar sesión…». | Pendiente | Pendiente | `T-01_postman.png` |
| T-02 | Token | Token con payload alterado | GET `/auth/me` | 401; «El token no es válido». | Pendiente | Pendiente | `T-02_postman.png` |
| T-03 | Token | Token previo a cambio de secreto | Cambiar `app.jwt.secret`, reiniciar, GET `/auth/me` | 401; «El token no es válido». Restaurar secreto después. | Pendiente | Pendiente | `T-03_*.png` |
| T-04 | Token | Token vencido | Expiración temporal de 1 minuto y GET `/auth/me` después de esperar | 401; «El token ha expirado…». Restaurar 60 minutos. | Pendiente | Pendiente | `T-04_*.png` |
| T-05 | Token | JWT de prueba | Decodificar payload sin publicar el token | `sub`, `authorities`, `iat` y `exp` correctos; ningún dato sensible. | Pendiente | Pendiente | `T-05_payload.png` |
| P-01 | Permisos | Vendedor | POST, PUT y DELETE `/categorias` | 403 en las tres; «No tiene permisos…». | Pendiente | Pendiente | `P-01_*.png` |
| P-02 | Permisos | Almacenero | GET `/clientes` y POST `/ventas` | 403 en ambas. | Pendiente | Pendiente | `P-02_*.png` |
| P-03 | Permisos | Vendedor y almacenero | GET `/reportes/productos-mas-vendidos` | 403 en ambas por `@PreAuthorize`. | Pendiente | Pendiente | `P-03_*.png` |
| P-04 | Permisos | Admin | Una petición de categorías, clientes, ventas y reportes | 2xx en las cuatro. | Pendiente | Pendiente | `P-04_*.png` |
| U-01 | Usuarios | Admin | POST `/usuarios`: contraseña `abcdefgh`; luego `rolIds: []` | 400 en ambas, con detalle de validación. | Pendiente | Pendiente | `U-01_*.png` |
| U-02 | Usuarios | Admin | POST `/usuarios` para empleado con cuenta; luego empleado libre, comprobar Oracle | 409 y luego 201; respuesta sin contraseña, hash BCrypt y fila en `usuario_roles`. | Pendiente | Pendiente | `U-02_*.png` |
| C-01 | CORS | SPA en `localhost:4200` | DevTools: OPTIONS previo a GET autenticado | OPTIONS 200; petición real 200 o 401; sin error CORS. | Pendiente | Pendiente | `C-01_devtools.png` |
| A-05 | Autenticación · propio | Sin contraseña | POST `/auth/login` | 400; campo `password` inválido. | Pendiente | Pendiente | `A-05_postman.png` |
| T-06 | Token · propio | `Bearer` sin JWT | GET `/auth/me` | 401; token inválido. | Pendiente | Pendiente | `T-06_postman.png` |
| P-05 | Permisos · propio | Vendedor | GET `/roles` | 403; administración reservada al ADMIN. | Pendiente | Pendiente | `P-05_postman.png` |
| U-03 | Usuarios · propio | Vendedor | POST `/usuarios` | 403; usuario sin permiso `USUARIOS_ADMINISTRAR`. | Pendiente | Pendiente | `U-03_postman.png` |
| B-01 | Contraseña | Vendedor | PUT `/auth/password` con contraseña actual y nueva válida | 204, sin cuerpo; login con la nueva contraseña 200. | Pendiente | Pendiente | `B-01_*.png` |
| B-02 | Contraseña | Vendedor | PUT `/auth/password` con contraseña actual errónea | 409; «La contraseña actual no es correcta». | Pendiente | Pendiente | `B-02_postman.png` |
| B-03 | Contraseña | Vendedor | PUT `/auth/password` con nueva igual a actual | 409; «La nueva contraseña debe ser distinta de la actual». | Pendiente | Pendiente | `B-03_postman.png` |
| B-04 | Contraseña | Vendedor | PUT `/auth/password` con nueva `abcdefgh` | 400; falta un número. | Pendiente | Pendiente | `B-04_postman.png` |
| B-05 | Roles | Admin; usuario de prueba | PUT `/usuarios/{id}/roles`, `rolIds:[2,3]`; usar token anterior del usuario | 200, roles y permisos nuevos; siguiente petición autorizada según roles actuales. | Pendiente | Pendiente | `B-05_*.png` |
| B-06 | Roles | Admin | Roles vacíos, rol inexistente y usuario inexistente | 400, 404 y 404 respectivamente. | Pendiente | Pendiente | `B-06_*.png` |
| B-07 | Estado | Admin; usuario de prueba | PATCH `/usuarios/{id}/estado`, `false`; probar token antiguo y login | 200 con `estado:false`; token antiguo 401 «El usuario está deshabilitado»; login 401 genérico. | Pendiente | Pendiente | `B-07_*.png` |
| B-08 | Autoprotección | Admin | Quitar su propio ADMIN; desactivar su propia cuenta | 409 en ambos casos. | Pendiente | Pendiente | `B-08_*.png` |

## Orden recomendado

1. Ejecuta A, T y P. Para T-03 y T-04 vuelve a la configuración original tras cada prueba.
2. Usa `GET /empleados` y `GET /usuarios` para escoger un empleado libre y un usuario de prueba. Los IDs dependen de tu base de datos; no asumas que María sigue sin cuenta.
3. Ejecuta U-02 y luego B-05 a B-07 con una cuenta de prueba, porque cambian datos. Cambia B-01 cuando ya no necesites la contraseña inicial de vendedor; actualiza la variable local de Postman, sin guardar su valor en Git.
4. C-01 se captura en el navegador. Oculta la columna Authorization en las capturas si muestra el JWT.

## Recuento final (completar después de ejecutar)

| Grupo | Total | Pasa | Falla |
|---|---:|---:|---:|
| Autenticación | 5 | — | — |
| Token | 6 | — | — |
| Permisos | 5 | — | — |
| Usuarios | 3 | — | — |
| CORS | 1 | — | — |
| Contraseña, roles y estado | 8 | — | — |
| **Total** | **28** | **—** | **—** |
