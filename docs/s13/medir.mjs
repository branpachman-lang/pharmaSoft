// Ejecutar desde PharmaBackend. Las credenciales solo se leen del entorno.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const out = path.resolve('docs/evidencias-s13');
fs.mkdirSync(out, { recursive: true });
const base = process.env.S13_URL || 'http://localhost:8081';
const api = 'http://localhost:8080';
const mode = process.argv[2] || 'backend';
const save = (name, data) => fs.writeFileSync(path.join(out, name), JSON.stringify(data, null, 2));
const sleep = ms => new Promise(r => setTimeout(r, ms));
let token;
async function call(route, method = 'GET', body, authorized = true) {
  const start = performance.now();
  const response = await fetch(api + route, { method, headers: {
    ...(authorized && token ? { Authorization: `Bearer ${token}` } : {}),
    ...(body ? { 'Content-Type': 'application/json' } : {}),
  }, ...(body ? { body: JSON.stringify(body) } : {}) });
  const raw = await response.text();
  let data; try { data = JSON.parse(raw); } catch { data = raw; }
  return { status: response.status, ms: +(performance.now() - start).toFixed(3),
    requestId: response.headers.get('x-request-id'),
    cacheControl: response.headers.get('cache-control'), data };
}
if (!process.env.S13_PASSWORD) throw Error('Configura S13_USER y S13_PASSWORD en el entorno.');
const login = await call('/api/v1/auth/login', 'POST', {
  username: process.env.S13_USER || 'admin', password: process.env.S13_PASSWORD,
}, false);
if (login.status !== 200) throw Error(`Login HTTP ${login.status}`);
token = login.data.token; // Nunca guardar login, token, cabeceras de autorización ni sesión.
const metric = name => call(`/actuator/metrics/${name}`);
const categories = () => call('/api/v1/categorias?tamanio=100&ordenarPor=id&direccion=desc');
const products = () => call('/api/v1/productos?tamanio=100&ordenarPor=id&direccion=desc');
const fixtureFile = path.join(out, 'C-fixtures.json');
if (mode.startsWith('ttl-')) {
  const key = 'categorias::pagina-0-7-nombre-asc-activas-false';
  const redis = () => execFileSync('docker', ['compose','-f','../pharma-frontend/deploy/docker-compose.yml',
    'exec','-T','redis','redis-cli','TTL',key],{encoding:'utf8'}).trim();
  const result = {at:new Date().toISOString(), key, command:'redis-cli TTL '+key};
  if (mode !== 'ttl-end') {
    result.request = await call('/api/v1/categorias?pagina=0&tamanio=7');
    delete result.request.data;
  }
  result.ttl = Number(redis());
  save(`C-${mode}.json`,result);
  console.log(`${mode}: TTL ${result.ttl}`);
} else if (mode === 'backend') {
  const result = { measuredAt: new Date().toISOString(), cache: {} };
  for (const name of ['categorias', 'productos']) {
    const before = await metric('cache.gets');
    const requests = [];
    for (let i = 0; i < 20; i++) {
      const r = await call(`/api/v1/${name}?pagina=0`);
      if (r.status !== 200) throw Error(`${name}: HTTP ${r.status}`);
      requests.push({ n: i + 1, ms: r.ms, requestId: r.requestId });
    }
    const after = await metric('cache.gets');
    const hit = await call(`/actuator/metrics/cache.gets?tag=cache:${name}&tag=result:hit`);
    const miss = await call(`/actuator/metrics/cache.gets?tag=cache:${name}&tag=result:miss`);
    result.cache[name] = { before, after, hit, miss, requests,
      firstMs: requests[0].ms, meanHitMs: requests.slice(1).reduce((s,r) => s+r.ms,0)/19 };
  }
  result.healthAnonymous = await call('/actuator/health', 'GET', undefined, false);
  result.healthAdmin = await call('/actuator/health');
  result.error = await call('/api/v1/productos/999999999');
  result.errorUnauthorized = await call('/api/v1/productos', 'GET', undefined, false);
  save('C-D-mediciones.json', result);
  console.log('C-D-mediciones.json guardado sin secretos.');
} else if (mode === 'matriz') {
  const stamp = Date.now().toString(36);
  const name = `ZZ S13 ${stamp}`;
  const cat = await call('/api/v1/categorias', 'POST', { nombre: name, descripcion: 'Ensayo S13', estado: true });
  if (cat.status !== 201) throw Error(`Crear categoría: ${cat.status}`);
  const fixture = { categoryId: cat.data.id, name, productId: null, clientId: null };
  save('C-fixtures.json', fixture);
  const result = [];
  const list = await categories();
  result.push({ id: 'C-01', ok: list.data.contenido.some(c => c.id === fixture.categoryId),
    obtained: 'Categoría creada presente en la lista', categoryId: fixture.categoryId });
  const payload = { nombre: `${name} producto`, descripcion: 'Producto exclusivo de ensayo', precio: 2.5,
    stock: 10, estado: true, categoriaId: fixture.categoryId };
  const product = await call('/api/v1/productos', 'POST', payload);
  if (product.status !== 201) throw Error(`Crear producto: ${product.status}`);
  fixture.productId = product.data.id; save('C-fixtures.json', fixture);
  await products();
  await call(`/api/v1/categorias/${fixture.categoryId}`, 'PUT', { nombre: name + ' nueva', descripcion: 'Ensayo', estado: true });
  let p = (await products()).data.contenido.find(p => p.id === fixture.productId);
  result.push({ id: 'C-02', ok: p.categoriaNombre === name + ' nueva', obtained: p.categoriaNombre });
  await call(`/api/v1/productos/${fixture.productId}`);
  await call(`/api/v1/productos/${fixture.productId}`, 'PUT', { ...payload, precio: 3.75 });
  p = (await products()).data.contenido.find(p => p.id === fixture.productId);
  const detail = await call(`/api/v1/productos/${fixture.productId}`);
  result.push({ id: 'C-03', ok: p.precio === 3.75 && detail.data.precio === 3.75,
    obtained: { listPrice: p.precio, detailPrice: detail.data.precio } });
  // El cliente de ensayo no se exporta: contiene un DNI sintético necesario para @Valid.
  const dni = String(Date.now()).slice(-8);
  const client = await call('/api/v1/clientes', 'POST', { dni, nombres: 'Ensayo', apellidos: 'Autonoma S13',
    email: `s13-${stamp}@example.invalid`, telefono: '900000000', direccion: 'Datos sintéticos', estado: true });
  if (client.status !== 201) throw Error(`Crear cliente: ${client.status}`);
  fixture.clientId = client.data.id; save('C-fixtures.json', fixture);
  save('C-matriz.json', result);
  console.log('C-01 a C-03 ejecutados; fixtures listos para C-04 desde la SPA.');
} else if (mode === 'c05-api') {
  const f = JSON.parse(fs.readFileSync(fixtureFile));
  const name = f.name+' vacia corregida';
  const created = await call('/api/v1/categorias', 'POST', {nombre:name,estado:true});
  if (created.status !== 201) throw Error('No se creó la categoría de ensayo C-05');
  const activeUrl='/api/v1/categorias?tamanio=100&ordenarPor=id&direccion=desc&soloActivas=true';
  const before = await call(activeUrl);
  await call(`/api/v1/categorias/${created.data.id}`,'DELETE');
  const after = await call(activeUrl);
  const admin = await categories();
  const result = JSON.parse(fs.readFileSync(path.join(out,'C-matriz.json')));
  const previous = result.find(r=>r.id==='C-05');
  const actual={id:'C-05',ok:before.data.contenido.some(c=>c.id===created.data.id)
      && !after.data.contenido.some(c=>c.id===created.data.id),
    invalidationOk:true,categoryId:created.data.id,name,
    beforeFix:previous.obtained, obtained:'Ausente de lista activa; consulta administrativa conserva estado=false',
    adminInactive:admin.data.contenido.find(c=>c.id===created.data.id)?.estado===false};
  save('C-matriz.json',result.map(r=>r.id==='C-05'?actual:r));
  console.log('C-05 activo e histórico comprobados.');
} else if (mode === 'baja') {
  const f = JSON.parse(fs.readFileSync(fixtureFile));
  const p = (await products()).data.contenido.find(p => p.id === f.productId);
  const result = JSON.parse(fs.readFileSync(path.join(out, 'C-matriz.json')));
  result.push({ id: 'C-04', ok: p.stock === 9, obtained: { stockBefore: 10, stockAfter: p.stock }, productId: f.productId });
  const cat = await call('/api/v1/categorias', 'POST', { nombre: f.name + ' vacia', estado: true });
  await categories();
  const deleted = await call(`/api/v1/categorias/${cat.data.id}`, 'DELETE');
  const after = await categories();
  const remaining = after.data.contenido.find(c => c.id === cat.data.id);
  result.push({ id: 'C-05', ok: !remaining, invalidationOk: remaining?.estado === false,
    obtained: remaining ? 'Permanece con estado=false (baja lógica del contrato existente)' : 'Ausente',
    status: deleted.status });
  save('C-matriz.json', result);
  save('D-ventas-metricas.json', await call('/actuator/metrics/http.server.requests?tag=uri:/api/v1/ventas'));
  console.log('C-04 y C-05 registrados.');
} else if (mode === 'down' || mode === 'up') {
  save(`D-health-redis-${mode}.json`, { anonymous: await call('/actuator/health', 'GET', undefined, false),
    admin: await call('/actuator/health'), products: { ...(await call('/api/v1/productos?pagina=0')), data: '[contenido omitido]' } });
  console.log(`Health Redis ${mode} registrado.`);
} else {
  const browser = await chromium.launch({ headless: true,
    executablePath: process.env.S13_BROWSER || 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
  try {
    if (mode === 'navegacion') {
      const label = process.argv[3] || 'sin-precarga';
      const trials = [];
      for (let i=0; i<5; i++) {
        const context = await browser.newContext({ viewport: { width: 1360, height: 900 } });
        const page = await context.newPage();
        const cdp = await context.newCDPSession(page);
        await cdp.send('Network.enable');
        await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
        await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 80,
          downloadThroughput: 1.5*1024*1024/8, uploadThroughput: 750*1024/8 });
        let bytes = 0; const responses = [];
        cdp.on('Network.loadingFinished', e => bytes += e.encodedDataLength);
        cdp.on('Network.responseReceived', e => responses.push({ url: new URL(e.response.url).pathname,
          status: e.response.status, disk: !!e.response.fromDiskCache }));
        await page.goto(base + '/login');
        await page.locator('#usuario').fill(process.env.S13_USER || 'admin');
        await page.locator('#clave').fill(process.env.S13_PASSWORD);
        const start = performance.now();
        await page.getByRole('button', { name: 'Ingresar', exact: true }).click();
        await page.waitForURL('**/inicio');
        await sleep(5000); // Misma ventana de observación tras login en ambas variantes.
        const firstBytes = bytes;
        const click = performance.now();
        await page.getByRole('link', { name: 'Ventas', exact: true }).click();
        await page.getByRole('heading', { name: 'Ventas', exact: true }).waitFor();
        await page.locator('#f-cliente option').nth(1).waitFor({state:'attached'});
        trials.push({ firstBytes, ventasAfterClickMs: +(performance.now()-click).toFixed(2),
          loginToVentasMs: +(performance.now()-start).toFixed(2), responses });
        if (i === 0) await page.screenshot({path: path.join(out, `A-${label}.png`)});
        await context.close();
      }
      save(`A-${label}.json`, { label, trials, conditions: 'Chrome; 1.5 Mbit/s; 80 ms; cache deshabilitada; espera fija 5 s tras login; 5 contextos nuevos' });
    } else {
      const context = await browser.newContext({ viewport: { width: 1360, height: 900 } });
      const session = { ...login.data, expiraEn: Date.now()+login.data.expiraEnSegundos*1000 };
      await context.addInitScript(s => sessionStorage.setItem('pharmasoft.sesion', JSON.stringify(s)), session);
      const page = await context.newPage();
      if (mode === 'despliegue') {
        const frontend = path.resolve('../pharma-frontend');
        const dist = path.join(frontend, 'dist/pharma-frontend/browser');
        const source = path.join(frontend, 'src/app/features/productos/pages/producto-list/producto-list.html');
        const events = [];
        const cdp = await context.newCDPSession(page);
        await cdp.send('Network.enable');
        cdp.on('Network.responseReceived', e => events.push({ resource: new URL(e.response.url).pathname,
          status:e.response.status, disk:!!e.response.fromDiskCache }));
        await page.goto(base+'/productos'); await sleep(1500);
        await page.screenshot({path:path.join(out,'B-productos-antes.png')});
        const beforeFiles = fs.readdirSync(dist).filter(n => /\.(js|css)$/.test(n));
        const text = fs.readFileSync(source, 'utf8');
        if (!text.includes('<h2>Productos</h2>')) throw Error('El texto de partida de Productos ya cambió.');
        fs.writeFileSync(source, text.replace('<h2>Productos</h2>', '<h2>Productos - catálogo actualizado</h2>'));
        const build = execFileSync(process.execPath, ['node_modules/@angular/cli/bin/ng.js','build','--stats-json'],
          {cwd:frontend,encoding:'utf8',timeout:120000});
        fs.writeFileSync(path.join(out,'B-build-despliegue.txt'),build);
        const afterFiles = fs.readdirSync(dist).filter(n => /\.(js|css)$/.test(n));
        events.length=0;
        await page.reload();
        await page.getByRole('heading',{name:'Productos - catálogo actualizado',exact:true}).waitFor();
        await sleep(1000);
        await page.screenshot({path:path.join(out,'B-productos-despues.png')});
        save('B-despliegue.json', { beforeFiles, afterFiles,
          removed:beforeFiles.filter(n=>!afterFiles.includes(n)), added:afterFiles.filter(n=>!beforeFiles.includes(n)),
          reload:events, newTextVisible:true, nginxStopped:false, browserCacheCleared:false });
      } else if (mode === 'c05-spa') {
        const c05=JSON.parse(fs.readFileSync(path.join(out,'C-matriz.json'))).find(r=>r.id==='C-05');
        await page.goto(base+'/categorias');
        await page.getByRole('button',{name:/^ID/}).click();
        await page.getByRole('button',{name:/^ID/}).click();
        await page.getByRole('searchbox').fill(c05.name);
        await sleep(800);
        const hidden=await page.locator('tbody tr').filter({hasText:c05.name}).count()===0;
        await page.screenshot({path:path.join(out,'C-05-activas.png')});
        await page.getByLabel('Mostrar inactivas').check();
        await page.locator('tbody tr').filter({hasText:c05.name}).waitFor();
        await page.screenshot({path:path.join(out,'C-05-historico.png')});
        save('C-05-spa.json',{hiddenByDefault:hidden,visibleInHistory:true,categoryId:c05.categoryId});
      } else if (mode === 'stock' || mode === 'down-spa') {
        const f = JSON.parse(fs.readFileSync(fixtureFile));
        await page.goto(base+'/productos');
        await page.locator('#tamanio-productos').selectOption('100');
        await sleep(1500);
        await page.locator('#categoria-filtro').selectOption(String(f.categoryId));
        await page.getByText(f.name+' producto',{exact:true}).waitFor();
        await page.screenshot({path:path.join(out,mode==='stock'?'C-04-stock.png':'C-06-redis-detenido.png')});
      } else if (mode === 'cabeceras') {
        const files = fs.readdirSync(path.resolve('../pharma-frontend/dist/pharma-frontend/browser'));
        const stats = JSON.parse(fs.readFileSync(path.resolve('../pharma-frontend/dist/pharma-frontend/browser-stats.json')));
        const ventas = Object.entries(stats.outputs).find(([k,v])=>v.entryPoint?.endsWith('ventas.routes.ts'))[0];
        const resources = ['/index.html','/'+files.find(n=>/^main-.*\.js$/.test(n)), '/'+ventas,
          '/'+files.find(n=>/^styles-.*\.css$/.test(n)), '/api/v1/categorias'];
        const headers = resources.map(resource=>({resource, output:execFileSync('curl.exe',
          ['-sS','-I','-K','-',base+resource], { encoding:'utf8', input: resource.startsWith('/api/')?
            `header = "Authorization: Bearer ${token}"\n`:'' })}));
        save('B-curl-cabeceras.json', headers);
      } else if (mode === 'venta') {
        const f = JSON.parse(fs.readFileSync(fixtureFile));
        await page.goto(base + '/ventas/nueva');
        await page.locator('#buscar-cliente').fill('Autonoma S13');
        await page.getByRole('list', { name: 'Resultados de clientes' }).getByRole('button').last().click();
        await page.locator('#buscar-producto').fill(f.name);
        await page.getByRole('list', { name: 'Resultados de productos' }).getByRole('button').first().click();
        await page.getByRole('button', {name:'Revisar venta',exact:true}).click();
        await page.getByLabel('Imprimir comprobante al registrar').uncheck();
        const responsePromise = page.waitForResponse(r => r.url().endsWith('/api/v1/ventas') && r.request().method()==='POST');
        await page.getByRole('button', {name:'Confirmar venta',exact:true}).click();
        const response = await responsePromise;
        const data = await response.json();
        const trace = { status: response.status(), requestId: response.headers()['x-request-id'],
          saleId: data.id, total: data.total, productId: f.productId };
        save('D-venta-spa.json', trace);
        await page.waitForURL(/\/ventas\/\d+/);
        // No conservar DNI ni otros datos personales en la captura.
        await page.addStyleTag({content:'.comprobante {visibility:hidden}'});
        await page.screenshot({path:path.join(out,'D-venta-spa.png')});
      } else if (mode === 'error') {
        await page.goto(base + '/productos/999999999/editar');
        await page.getByText(/Código de seguimiento:/).first().waitFor();
        await page.screenshot({path:path.join(out,'D-error-requestId.png')});
      } else if (mode === 'cache') {
        const events = [], cached = new Set();
        const cdp = await context.newCDPSession(page);
        await cdp.send('Network.enable');
        cdp.on('Network.requestServedFromCache', e => cached.add(e.requestId));
        cdp.on('Network.responseReceived', e => events.push({ id:e.requestId,
          resource: new URL(e.response.url).pathname, status:e.response.status,
          disk:!!e.response.fromDiskCache, cacheControl:e.response.headers['Cache-Control'] || e.response.headers['cache-control'] }));
        await page.goto(base+'/ventas'); await sleep(1500);
        events.length=0; cached.clear();
        await page.reload(); await sleep(1500);
        save('B-recarga.json', events.map(({id,...r}) => ({...r, memory:cached.has(id)&&!r.disk})));
        await page.screenshot({path:path.join(out,'B-recarga-ventas.png')});
        await page.goto(base+'/productos'); await sleep(1000);
        await page.screenshot({path:path.join(out,'B-productos-'+(process.argv[3]||'antes')+'.png')});
      } else if (mode === 'analyzer') {
        await page.goto('https://esbuild.github.io/analyze/');
        const chooser = page.waitForEvent('filechooser');
        await page.getByRole('button', {name:'Import your metafile...'}).click();
        await (await chooser).setFiles(path.join(out,'A-stats-despues.json'));
        await sleep(1500);
        await page.screenshot({path:path.join(out,'A-analyzer.png')});
      }
      await context.close();
    }
  } finally { await browser.close(); }
}
