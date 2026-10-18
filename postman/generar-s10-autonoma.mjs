import fs from 'node:fs';
import path from 'node:path';

const variables = [
  ['baseUrl', 'http://localhost:8080/api/v1'],
  ['adminPassword', 'Admin2026*'], ['vendedorPassword', 'Vendedor2026*'],
  ['almacenPassword', 'Almacen2026*'], ['supervisorPassword', 'Supervisor2026*'],
  ['inactivoPassword', 'Inactivo2026*'], ['passwordNueva', 'NuevaClave2026'],
  ['tokenAdmin', ''], ['tokenVendedor', ''], ['tokenAlmacen', ''],
  ['tokenSupervisor', ''], ['tokenInactivo', ''], ['tokenAlterado', ''],
  ['tokenAnteriorSecreto', ''], ['tokenExpirable', ''],
  ['categoriaId', '1'], ['usuarioId', ''], ['adminId', '1'],
  ['usuarioPruebaUsername', 's10_nuevo'], ['usuarioPruebaPassword', 'Prueba2026*'],
  ['empleadoConUsuarioId', ''], ['empleadoLibreId', ''], ['rolInexistenteId', '999999'],
  ['clienteId', '1'], ['productoId', '1']
].map(([key, value]) => ({ key, value, type: 'string' }));

const folders = new Map();
function request(id, group, title, method, route, token, body, expected, note = '', script = '') {
  const header = [];
  if (token !== null) header.push({ key: 'Authorization', value: token, type: 'text' });
  if (body !== undefined) header.push({ key: 'Content-Type', value: 'application/json', type: 'text' });
  const item = {
    name: `${id} · ${title}`,
    request: {
      method, header,
      // Postman importa la URL como texto y muestra {{baseUrl}} directamente
      // en la barra de la petición. El objeto {raw: ...} se veía vacío en
      // algunas versiones de la aplicación de escritorio.
      url: `{{baseUrl}}${route}`,
      description: `Resultado esperado: ${expected}. ${note}`
    },
    event: [{ listen: 'test', script: { type: 'text/javascript', exec: [
      `pm.test('HTTP ${expected}', () => pm.response.to.have.status(${expected}));`,
      ...script.split('\n').filter(Boolean)
    ] } }]
  };
  if (body !== undefined) item.request.body = { mode: 'raw', raw: JSON.stringify(body, null, 2), options: { raw: { language: 'json' } } };
  if (!folders.has(id)) folders.set(id, { name: `${id} · ${group}`, item: [] });
  folders.get(id).item.push(item);
}
function login(id, title, username, passVar, expected, saveTo = '') {
  const script = saveTo ? `if (pm.response.code === 200) pm.collectionVariables.set('${saveTo}', pm.response.json().token);` : '';
  request(id, 'Autenticación', title, 'POST', '/auth/login', null,
    { username, password: `{{${passVar}}}` }, expected,
    saveTo ? `Guarda el JWT en ${saveTo} para esta ejecución.` : '', script);
}
const admin = 'Bearer {{tokenAdmin}}';
const vendedor = 'Bearer {{tokenVendedor}}';
const almacen = 'Bearer {{tokenAlmacen}}';
const categoria = { nombre: 'Prueba seguridad S10', descripcion: 'Solicitud de permiso denegado', estado: true };
const venta = { clienteId: '{{clienteId}}', detalles: [{ productoId: '{{productoId}}', cantidad: 1 }] };

login('A-01', 'Login admin', 'admin', 'adminPassword', 200, 'tokenAdmin');
login('A-01', 'Login vendedor', 'vendedor', 'vendedorPassword', 200, 'tokenVendedor');
login('A-01', 'Login almacenero', 'almacenero', 'almacenPassword', 200, 'tokenAlmacen');
login('A-01', 'Login supervisor', 'supervisor', 'supervisorPassword', 200, 'tokenSupervisor');
request('A-02', 'Autenticación', 'Usuario inexistente', 'POST', '/auth/login', null, { username: 'no_existe_s10', password: 'Prueba2026*' }, 401);
request('A-02', 'Autenticación', 'Contraseña equivocada', 'POST', '/auth/login', null, { username: 'admin', password: 'Incorrecta2026' }, 401);
login('A-03', 'Login inactivo', 'inactivo', 'inactivoPassword', 401);
login('A-04', 'Username en mayúsculas', 'VENDEDOR', 'vendedorPassword', 200);
request('A-05', 'Autenticación propia', 'Contraseña vacía', 'POST', '/auth/login', null, { username: 'admin', password: '' }, 400);

request('T-01', 'Token', 'Sin prefijo Bearer', 'GET', '/auth/me', '{{tokenAdmin}}', undefined, 401);
request('T-02', 'Token', 'Payload alterado', 'GET', '/auth/me', 'Bearer {{tokenAlterado}}', undefined, 401,
  'Pega en tokenAlterado un JWT cuyo segmento central tenga un carácter cambiado. No guardes el valor en Git.');
request('T-03', 'Token', 'Secreto modificado', 'GET', '/auth/me', 'Bearer {{tokenAnteriorSecreto}}', undefined, 401,
  'Antes: copia tokenAdmin en tokenAnteriorSecreto, cambia temporalmente app.jwt.secret, reinicia y luego restaura el secreto.');
request('T-04', 'Token', 'Token vencido', 'GET', '/auth/me', 'Bearer {{tokenExpirable}}', undefined, 401,
  'Configura expiración de 1 minuto, inicia sesión, copia el JWT en tokenExpirable, espera más de 60 s, prueba y restaura 60 minutos.');
request('T-05', 'Token', 'Inspección del payload JWT', 'GET', '/auth/me', admin, undefined, 200,
  'En Postman Console inspecciona solo el objeto claims; oculta el JWT completo en la captura.',
  "const jwt=pm.collectionVariables.get('tokenAdmin'); if(jwt){const claims=JSON.parse(atob(jwt.split('.')[1].replace(/-/g,'+').replace(/_/g,'/'))); console.log({sub:claims.sub,authorities:claims.authorities,iat:claims.iat,exp:claims.exp}); pm.test('Claims esenciales',()=>pm.expect(claims).to.include.all.keys('sub','authorities','iat','exp')); pm.test('Sin contraseña',()=>pm.expect(JSON.stringify(claims).toLowerCase()).not.to.include('password'));}");
request('T-06', 'Token propio', 'Bearer vacío', 'GET', '/auth/me', 'Bearer ', undefined, 401);

request('P-01', 'Permisos', 'Vendedor crea categoría', 'POST', '/categorias', vendedor, categoria, 403);
request('P-01', 'Permisos', 'Vendedor modifica categoría', 'PUT', '/categorias/{{categoriaId}}', vendedor, categoria, 403);
request('P-01', 'Permisos', 'Vendedor elimina categoría', 'DELETE', '/categorias/{{categoriaId}}', vendedor, undefined, 403);
request('P-02', 'Permisos', 'Almacenero lee clientes', 'GET', '/clientes', almacen, undefined, 403);
request('P-02', 'Permisos', 'Almacenero registra venta', 'POST', '/ventas', almacen, venta, 403);
request('P-03', 'Permisos', 'Vendedor consulta reporte', 'GET', '/reportes/productos-mas-vendidos', vendedor, undefined, 403);
request('P-03', 'Permisos', 'Almacenero consulta reporte', 'GET', '/reportes/productos-mas-vendidos', almacen, undefined, 403);
for (const [title, route] of [['categorías','/categorias'],['clientes','/clientes'],['ventas','/ventas'],['reportes','/reportes/productos-mas-vendidos']])
  request('P-04', 'Permisos', `Admin consulta ${title}`, 'GET', route, admin, undefined, 200);
request('P-05', 'Permisos propios', 'Vendedor lee roles', 'GET', '/roles', vendedor, undefined, 403);

request('U-01', 'Usuarios', 'Contraseña sin número', 'POST', '/usuarios', admin,
  { username: 's10_invalido_1', password: 'abcdefgh', empleadoId: '{{empleadoLibreId}}', rolIds: [2] }, 400);
request('U-01', 'Usuarios', 'Sin roles', 'POST', '/usuarios', admin,
  { username: 's10_invalido_2', password: 'Prueba2026*', empleadoId: '{{empleadoLibreId}}', rolIds: [] }, 400);
request('U-02', 'Usuarios', 'Empleado con cuenta', 'POST', '/usuarios', admin,
  { username: 's10_duplicado', password: 'Prueba2026*', empleadoId: '{{empleadoConUsuarioId}}', rolIds: [2] }, 409);
request('U-02', 'Usuarios', 'Empleado libre', 'POST', '/usuarios', admin,
  { username: '{{usuarioPruebaUsername}}', password: '{{usuarioPruebaPassword}}', empleadoId: '{{empleadoLibreId}}', rolIds: [2] }, 201,
  'Comprueba además el hash y usuario_roles en SQL Developer.',
  "if(pm.response.code===201) pm.collectionVariables.set('usuarioId', String(pm.response.json().id));");
request('U-03', 'Usuarios propios', 'Vendedor crea usuario', 'POST', '/usuarios', vendedor,
  { username: 's10_sin_permiso', password: 'Prueba2026*', empleadoId: '{{empleadoLibreId}}', rolIds: [2] }, 403);

request('B-01', 'Contraseña', 'Cambio correcto', 'PUT', '/auth/password', vendedor,
  { passwordActual: '{{vendedorPassword}}', passwordNueva: '{{passwordNueva}}' }, 204,
  'Tras 204 la variable local vendedorPassword se actualiza; inicia sesión de nuevo para comprobar.',
  "if(pm.response.code===204) pm.collectionVariables.set('vendedorPassword', pm.collectionVariables.get('passwordNueva'));");
login('B-01', 'Nuevo login tras el cambio', 'vendedor', 'vendedorPassword', 200, 'tokenVendedor');
request('B-02', 'Contraseña', 'Contraseña actual incorrecta', 'PUT', '/auth/password', vendedor,
  { passwordActual: 'Incorrecta2026', passwordNueva: 'OtraClave2026' }, 409);
request('B-03', 'Contraseña', 'Nueva igual a la actual', 'PUT', '/auth/password', vendedor,
  { passwordActual: '{{vendedorPassword}}', passwordNueva: '{{vendedorPassword}}' }, 409);
request('B-04', 'Contraseña', 'Nueva sin número', 'PUT', '/auth/password', vendedor,
  { passwordActual: '{{vendedorPassword}}', passwordNueva: 'abcdefgh' }, 400);
request('B-05', 'Roles', 'Login del usuario antes de cambiar roles', 'POST', '/auth/login', null,
  { username: '{{usuarioPruebaUsername}}', password: '{{usuarioPruebaPassword}}' }, 200,
  'Conserva este token para probar el permiso nuevo sin volver a iniciar sesión.',
  "if(pm.response.code===200) pm.collectionVariables.set('tokenUsuarioPrueba', pm.response.json().token);");
request('B-05', 'Roles', 'Sin permiso de escritura antes del cambio', 'POST', '/categorias', 'Bearer {{tokenUsuarioPrueba}}',
  { nombre: 'S10 antes de roles {{$timestamp}}', descripcion: 'No debe crearse', estado: true }, 403);
request('B-05', 'Roles', 'Asignar VENDEDOR y ALMACENERO', 'PUT', '/usuarios/{{usuarioId}}/roles', admin,
  { rolIds: [2,3] }, 200, 'Obtén antes el token del usuario de prueba y reúsalo en la siguiente petición.');
request('B-05', 'Roles', 'Verificar roles con token anterior', 'GET', '/auth/me', 'Bearer {{tokenUsuarioPrueba}}', undefined, 200,
  'La respuesta debe mostrar los roles y permisos actuales.');
request('B-05', 'Roles', 'Permiso de escritura con token anterior', 'POST', '/categorias', 'Bearer {{tokenUsuarioPrueba}}',
  { nombre: 'S10 nuevo permiso {{$timestamp}}', descripcion: 'Prueba de cambio de roles', estado: true }, 201,
  'El mismo JWT debe permitir la escritura porque el filtro vuelve a leer los roles en cada petición.');
request('B-06', 'Roles', 'Conjunto vacío', 'PUT', '/usuarios/{{usuarioId}}/roles', admin, { rolIds: [] }, 400);
request('B-06', 'Roles', 'Rol inexistente', 'PUT', '/usuarios/{{usuarioId}}/roles', admin, { rolIds: ['{{rolInexistenteId}}'] }, 404);
request('B-06', 'Roles', 'Usuario inexistente', 'PUT', '/usuarios/999999/roles', admin, { rolIds: [2] }, 404);
request('B-07', 'Estado', 'Desactivar usuario', 'PATCH', '/usuarios/{{usuarioId}}/estado', admin, { estado: false }, 200);
request('B-07', 'Estado', 'Token previo del desactivado', 'GET', '/auth/me', 'Bearer {{tokenUsuarioPrueba}}', undefined, 401);
request('B-07', 'Estado', 'Login del desactivado', 'POST', '/auth/login', null,
  { username: '{{usuarioPruebaUsername}}', password: '{{usuarioPruebaPassword}}' }, 401);
request('B-08', 'Autoprotección', 'Admin se quita ADMIN', 'PUT', '/usuarios/{{adminId}}/roles', admin,
  { rolIds: [2] }, 409);
request('B-08', 'Autoprotección', 'Admin se desactiva', 'PATCH', '/usuarios/{{adminId}}/estado', admin,
  { estado: false }, 409);

// C-01 requiere DevTools porque el navegador, no Postman, realiza el preflight CORS.
folders.set('C-01', { name: 'C-01 · CORS en SPA (DevTools)', description: 'Abre la SPA en localhost:4200 y captura OPTIONS + GET en Network. Postman no reproduce la política CORS del navegador.', item: [] });
variables.push({ key: 'tokenUsuarioPrueba', value: '', type: 'string' });

const collection = {
  info: {
    name: 'PharmaSoft - S10 Seguridad autónoma',
    description: '28 casos de la actividad autónoma. Ejecutar en orden, completar los IDs según la base local y guardar capturas. Los JWT no se incluyen en este archivo. A-01 guarda tokens locales mediante scripts de prueba. U-02, B-01, B-05 y B-07 modifican datos; T-03 y T-04 requieren cambios temporales de configuración. C-01 se captura en la SPA.',
    schema: 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
  },
  variable: variables,
  item: [...folders.values()]
};
const output = path.join(import.meta.dirname, 'PharmaSoft-S10-Seguridad.json');
fs.writeFileSync(output, JSON.stringify(collection, null, 2) + '\n', 'utf8');
console.log(`Colección generada: ${output} (${folders.size} casos, ${collection.item.reduce((n,x)=>n+x.item.length,0)} peticiones)`);
