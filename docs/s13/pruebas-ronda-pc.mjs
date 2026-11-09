// API y Redis reales. La SPA y las capturas se operan aparte en Edge instalado.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const out=path.resolve('docs/evidencias-s13-autonoma-manual/2026-11-08-control-pc');
fs.mkdirSync(out,{recursive:true});
const save=(name,data)=>fs.writeFileSync(path.join(out,name),JSON.stringify(data,null,2));
const command=process.argv[2];
const api='http://localhost:8080';
let token;
async function call(url,{method='GET',body,auth=true}={}) {
  const start=performance.now();
  const r=await fetch(url.startsWith('http')?url:api+url,{method,headers:{
    ...(auth&&token?{Authorization:`Bearer ${token}`} : {}),
    ...(body?{'Content-Type':'application/json'}:{})},...(body?{body:JSON.stringify(body)}:{})});
  const text=await r.text();let data;
  try{data=JSON.parse(text);}catch{data=text;}
  return {url,status:r.status,ms:+(performance.now()-start).toFixed(3),
    requestId:r.headers.get('x-request-id'),headers:Object.fromEntries(r.headers),data};
}
if (!process.env.S13_PASSWORD) throw Error('Configura S13_PASSWORD en memoria.');
const login=await call('/api/v1/auth/login',{method:'POST',body:{username:'admin',password:process.env.S13_PASSWORD},auth:false});
if(login.status!==200)throw Error(`Login HTTP ${login.status}`);
token=login.data.token; // Nunca persistir esta respuesta ni imprimir el token.
const docker=(args)=>execFileSync('docker',['compose','-f','../pharma-frontend/deploy/docker-compose.yml','exec','-T','redis','redis-cli',...args],{encoding:'utf8'}).trim();
const count=async(name,result)=>call(`/actuator/metrics/cache.gets?tag=name:${name}&tag=result:${result}`);
const val=r=>r.data?.measurements?.find(m=>m.statistic==='COUNT')?.value ?? 0;
if(command==='cache') {
  const records={fecha:new Date().toISOString(),metodo:'20 GET secuenciales, cliente Node, tiempo total HTTP, deltas por caché',caches:{}};
  for(const name of ['categorias','productos']) {
    const key=`${name}::pagina-0-10-nombre-asc${name==='categorias'?'-activas-false':''}`;
    docker(['DEL',key]);
    const before={hit:await count(name,'hit'),miss:await count(name,'miss')};
    const trials=[];
    for(let i=1;i<=20;i++) {
      const r=await call(`/api/v1/${name}?pagina=0&tamanio=10&ordenarPor=nombre&direccion=asc${name==='categorias'?'&soloActivas=false':''}`);
      if(r.status!==200)throw Error(`${name} devolvió ${r.status}`);
      trials.push({n:i,status:r.status,ms:r.ms,requestId:r.requestId});
    }
    const after={hit:await count(name,'hit'),miss:await count(name,'miss')};
    const hits=val(after.hit)-val(before.hit),misses=val(after.miss)-val(before.miss);
    records.caches[name]={key,before,after,trials,hits,misses,rate:100*hits/(hits+misses),
      firstMs:trials[0].ms,meanHitMs:trials.slice(1).reduce((s,r)=>s+r.ms,0)/19};
  }
  save('C01-C02-series-20.json',records);
  console.log(JSON.stringify(Object.fromEntries(Object.entries(records.caches).map(([n,v])=>[n,{hits:v.hits,misses:v.misses,rate:v.rate,firstMs:v.firstMs,meanHitMs:v.meanHitMs}]))));
} else if(command==='health-on'||command==='health-off') {
  const products=await call('/api/v1/productos?pagina=0');
  const result={fecha:new Date().toISOString(),publico:await call('/actuator/health',{auth:false}),
    admin:await call('/actuator/health'),productos:{...products,data:{filas:products.data?.contenido?.length}}};
  save(`C09-${command}.json`,result);console.log(JSON.stringify({health:result.publico.status,status:result.publico.data.status,productos:products.status}));
} else if(command.startsWith('ttl')) {
  const key='categorias::pagina-0-7-nombre-asc-activas-false';
  const before=Number(docker(['TTL',key]));
  if(command!=='ttl-expirada') {docker(['DEL',key]);await call('/api/v1/categorias?pagina=0&tamanio=7&ordenarPor=nombre&direccion=asc&soloActivas=false');}
  const result={fecha:new Date().toISOString(),clave:key,ttlAntes:before,ttl:Number(docker(['TTL',key])),comando:'redis-cli TTL '+key};
  save('C03-'+command+'.json',result);console.log(JSON.stringify(result));
} else if(command==='comprobar') {
  const ui=JSON.parse(fs.readFileSync(path.join(out,'ronda-ui.json')));
  const producto=await call('/api/v1/productos/'+ui.productoId);
  const listado=await call('/api/v1/productos?tamanio=100&ordenarPor=id&direccion=desc');
  const activo=await call('/api/v1/categorias?tamanio=100&ordenarPor=id&direccion=desc&soloActivas=true');
  const historico=await call('/api/v1/categorias/'+ui.vaciaId);
  const venta=await call('/api/v1/ventas/'+ui.ventaId);
  save('C-matriz-api.json',{fecha:new Date().toISOString(),producto,productoLista:listado.data.contenido.find(p=>p.id===ui.productoId),
    bajaAusenteDeActivas:!activo.data.contenido.some(c=>c.id===ui.vaciaId),bajaHistorico:historico,venta});
  const errores={noEncontrado:await call('/api/v1/productos/999999999'),sinToken:await call('/api/v1/productos',{auth:false}),
    validacion:await call('/api/v1/categorias',{method:'POST',body:{nombre:'',descripcion:'Ensayo rechazo',estado:true}}),
    stockInsuficiente:await call('/api/v1/ventas',{method:'POST',body:{clienteId:venta.data.clienteId,detalles:[{productoId:ui.productoId,cantidad:100000}]}})};
  save('D02-errores-api.json',errores);
  save('D04-metricas-ventas.json',{uri:await call('/actuator/metrics/http.server.requests?tag=uri:/api/v1/ventas'),
    post:await call('/actuator/metrics/http.server.requests?tag=uri:/api/v1/ventas&tag=method:POST')});
  const log=fs.readFileSync('logs/pharma-backend.log','utf8');
  const saleLine=log.split(/\r?\n/).find(l=>l.includes(`ventaId=${ui.ventaId} |`));
  const id=saleLine?.match(/\[([a-f0-9]{8})\]/)?.[1];
  if(!id)throw Error('No se encontró la traza de la venta');
  const trace=log.split(/\r?\n/).filter(l=>l.includes('['+id+']'));
  fs.writeFileSync(path.join(out,'D01-traza-venta.txt'),trace.join('\n'));
  save('D01-identificadores.json',{ventaId:ui.ventaId,requestId:id,lineas:trace.length});
  const current=log.split(/\r?\n/).filter(l=>l.slice(0,19)>='2026-11-08 22:20:56');
  const patterns={palabras:/password|Bearer |secret/i,jwt:/\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/,dni:/DNI\s*[=:]\s*\d{8}\b/i};
  save('D03-auditoria.json',{fecha:new Date().toISOString(),archivo:'logs/pharma-backend.log',lineasRonda:current.length,
    conteos:Object.fromEntries(Object.entries(patterns).map(([n,re])=>[n,current.filter(l=>re.test(l)).length])),
    contrasenaDeEnsayo:current.filter(l=>l.includes(process.env.S13_PASSWORD)).length,
    alcance:'Ronda desde 22:20:56; conteos, sin líneas que contengan datos sensibles'});
  console.log(JSON.stringify({productoId:ui.productoId,precio:producto.data.precio,stock:producto.data.stock,
    categoria:producto.data.categoriaNombre,bajaInactiva:historico.data.estado===false,ventaId:ui.ventaId,requestId:id,
    errores:Object.fromEntries(Object.entries(errores).map(([n,r])=>[n,r.status]))}));
} else if(command==='headers') {
  const dist=path.resolve('../pharma-frontend/dist/pharma-frontend');
  const files=fs.readdirSync(path.join(dist,'browser'));
  const stats=JSON.parse(fs.readFileSync(path.join(dist,'browser-stats.json')));
  const ventas=Object.entries(stats.outputs).find(([k,v])=>v.entryPoint?.endsWith('ventas.routes.ts'))[0];
  const routes=['/index.html','/'+files.find(n=>/^main-.*\.js$/.test(n)),'/'+ventas,'/'+files.find(n=>/^styles-.*\.css$/.test(n)),'/api/v1/categorias'];
  const results=[];
  for(const r of routes) {
    const input=r.startsWith('/api/')?`header = "Authorization: Bearer ${token}"\n`:'';
    results.push({ruta:r,salidaCurl:execFileSync('curl.exe',['-sS','-I','-K','-','http://localhost:8081'+r],{input,encoding:'utf8'})});
  }
  save('B01-cabeceras-curl.json',results);console.log('Cinco cabeceras reales guardadas sin autorización.');
} else throw Error('Modo no reconocido');
