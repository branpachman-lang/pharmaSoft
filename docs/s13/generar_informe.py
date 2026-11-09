"""Informe S13 a partir de mediciones locales conservadas, sin valores inventados."""
from pathlib import Path
import json, re, statistics, collections, hashlib, html, shutil
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage, ImageDraw, ImageFont

DOCS = Path(__file__).resolve().parents[1]
ROOT = DOCS.parent
E = DOCS / 'evidencias-s13'
def data(name): return json.loads((E/name).read_text(encoding='utf-8-sig'))
def write(name, value): (E/name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def initial(name):
    stats = data(name)
    pending = [k for k,v in stats['outputs'].items() if v.get('entryPoint') == 'src/main.ts']
    visited = set()
    while pending:
        key = pending.pop()
        if key in visited: continue
        visited.add(key)
        pending += [i['path'] for i in stats['outputs'][key]['imports']
                    if i['kind'] != 'dynamic-import' and not i.get('external') and i['path'] in stats['outputs']]
    # Angular incluye también CSS de componentes virtuales en el metafile;
    # solo styles-*.css se entrega como hoja global inicial.
    visited.update(k for k in stats['outputs'] if k.startswith('styles-') and k.endswith('.css'))
    modules = collections.Counter()
    for k in visited:
        for name, value in stats['outputs'][k]['inputs'].items(): modules[name] += value['bytesInOutput']
    return {'bytes':sum(stats['outputs'][k]['bytes'] for k in visited),
            'outputs': sorted(visited), 'modules':modules.most_common(5)}

before = initial('A-stats-antes.json'); after = initial('A-stats-despues.json')
nav = {name:data('A-'+name+'.json') for name in ['sin-precarga','con-precarga']}
summary = {k:{'firstBytes':statistics.mean(t['firstBytes'] for t in v['trials']),
              'clickMs':statistics.mean(t['ventasAfterClickMs'] for t in v['trials']),
              'loginMs':statistics.mean(t['loginToVentasMs'] for t in v['trials'])} for k,v in nav.items()}
cache = data('C-D-mediciones.json')['cache']; matrix = data('C-matriz.json')
down = data('D-health-redis-down.json'); up = data('D-health-redis-up.json')
if not any(row['id']=='C-06' for row in matrix):
    matrix.append({'id':'C-06','ok':down['products']['status']==200 and down['anonymous']['data']['status']=='DOWN',
                   'obtained':{'productsStatus':down['products']['status'],'healthStatus':down['anonymous']['status'],
                               'health':down['anonymous']['data']['status'],'restored':up['anonymous']['data']['status']}})
    write('C-matriz.json',matrix)
trace = data('D-venta-spa.json'); deploy = data('B-despliegue.json')
ttl = [data('C-ttl-start.json'),data('C-ttl-end.json'),data('C-ttl-restored.json')]
log = (ROOT/'logs/pharma-backend.log').read_text(encoding='utf-8',errors='replace')
started = '2026-11-08 19:48:40'
current_lines = [s for s in log.splitlines() if s[:19] >= started]
patterns = {'palabras_password_bearer_secret':r'(?i)password|Bearer |secret',
            'JWT_completo':r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',
            'DNI_explicito_completo':r'(?i)DNI\s*[=:]\s*\d{8}\b'}
audit = {name:{'historico':sum(bool(re.search(pattern,s)) for s in log.splitlines()),
              'ejecucion_corregida':sum(bool(re.search(pattern,s)) for s in current_lines)}
         for name,pattern in patterns.items()}
audit['alcance'] = 'pharma-backend.log completo y líneas desde 2026-11-08 19:48:40; revisión estática de logs de ClienteServiceImpl y VentaServiceImpl'
write('D-auditoria.json',audit)
write('A-resumen.json',{'before':before,'after':after,'navigation':summary})

# Exportaciones gráficas de los datos capturados. Se distinguen de capturas de la SPA.
font_path = 'C:/Windows/Fonts/arial.ttf'
font_bold = 'C:/Windows/Fonts/arialbd.ttf'
def panel(name,title,lines):
    width=1400; line_height=38
    im=PILImage.new('RGB',(width,140+line_height*len(lines)), '#f4f7fb'); d=ImageDraw.Draw(im)
    d.rectangle((0,0,width,85),fill='#12365d')
    d.text((35,20),title,font=ImageFont.truetype(font_bold,30),fill='white')
    f=ImageFont.truetype(font_path,24)
    for i,line in enumerate(lines):d.text((35,110+i*line_height),line,font=f,fill='#172b42')
    im.save(E/name)

panel('A-medicion.png','A | Exportación de las compilaciones de producción',[
    f"Initial antes: {before['bytes']:,} bytes | después: {after['bytes']:,} bytes",
    f"Reducción: {before['bytes']-after['bytes']:,} bytes ({(1-after['bytes']/before['bytes'])*100:.2f} %)",
    *[f"{k}: primera pantalla {v['firstBytes']:.0f} B; clic a Ventas {v['clickMs']:.2f} ms" for k,v in summary.items()],
    'Fuente: browser-stats.json y Network de Chrome; 5 navegaciones por variante.'])
panel('C-aciertos.png','C | Exportación de las 20 consultas por caché',[
    *[f"{n}: 19 hit / 1 miss = 95 %; primero {v['firstMs']:.3f} ms; media hit {v['meanHitMs']:.3f} ms" for n,v in cache.items()],
    *[f"{v['command']} -> {v['ttl']} | {v['at']}" for v in ttl],
    'Fuente: Actuator, cliente HTTP y redis-cli del entorno de ensayo.'])
panel('D-health.png','D | Exportación de health y auditoría',[
    f"Redis encendido: público {up['anonymous']['status']} {up['anonymous']['data']['status']}; admin {up['admin']['status']}",
    f"Redis apagado: público {down['anonymous']['status']} {down['anonymous']['data']['status']}; admin {down['admin']['status']}",
    f"Productos con Redis apagado: HTTP {down['products']['status']}",
    *[f"{n}: histórico={v['historico']}; ejecución corregida={v['ejecucion_corregida']}" for n,v in audit.items() if isinstance(v,dict)],
    'Los logs históricos se auditan; no se reproducen datos personales en el informe.'])
panel('D-venta-log.png','D | Venta desde la SPA: X-Request-Id '+trace['requestId'],
      [(s.split('] ',1)[1] if '] ' in s else s) for s in (E/'D-venta-traza.txt').read_text().splitlines()])
header_rows=data('B-curl-cabeceras.json')
panel('B-cabeceras.png','B | Exportación de curl -I en Nginx 8081',[
    text for item in header_rows for text in [item['resource'],
    '  '+' | '.join(s.strip() for s in item['output'].splitlines() if s.startswith('HTTP/') or s.lower().startswith('cache-control:'))]])

pdfmetrics.registerFont(TTFont('Arial',font_path)); pdfmetrics.registerFont(TTFont('ArialBold',font_bold))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TextES',fontName='Arial',fontSize=9.5,leading=14,textColor=colors.HexColor('#203247'),spaceAfter=8))
styles.add(ParagraphStyle(name='TitleES',fontName='ArialBold',fontSize=27,leading=33,textColor=colors.HexColor('#12365d'),spaceAfter=18))
styles.add(ParagraphStyle(name='H1ES',fontName='ArialBold',fontSize=19,leading=24,textColor=colors.HexColor('#12365d'),spaceAfter=14))
styles.add(ParagraphStyle(name='H2ES',fontName='ArialBold',fontSize=12,leading=16,textColor=colors.HexColor('#166d7a'),spaceBefore=9,spaceAfter=7))
styles.add(ParagraphStyle(name='SmallES',fontName='Arial',fontSize=8,leading=11,spaceAfter=6,textColor=colors.HexColor('#526477')))
story=[]; md=[]
def p(text,style='TextES'):
    story.append(Paragraph(text,styles[style])); md.append(re.sub('<[^>]*>','',text)+'\n')
def title(text): p(text,'H1ES')
def h(text): p(text,'H2ES')
def page(): story.append(PageBreak()); md.append('\n---\n')
def table(headers, rows, widths=None):
    contents=[[Paragraph(html.escape(str(c)),styles['SmallES']) for c in row] for row in [headers]+rows]
    t=Table(contents,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e1edf5')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#12365d')),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LINEBELOW',(0,0),(-1,0),0.8,colors.HexColor('#b8cbd8')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f8fa')])]))
    story.append(t);story.append(Spacer(1,9))
    md.append('| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+
              '\n'.join('| '+' | '.join(str(c) for c in row)+' |' for row in rows)+'\n')
def pic(name,caption,width=475,maxheight=245,crop=None):
    im=PILImage.open(E/name); image_path=E/name
    if crop:
        im=im.crop(crop); image_path=DOCS.parents[1]/'tmp/pdfs'/('recorte-'+name)
        im.save(image_path)
    w,hg=im.size; scale=min(width/w,maxheight/hg)
    story.append(Image(str(image_path),width=w*scale,height=hg*scale,hAlign='LEFT'));p(caption,'SmallES')
    md.append(f'![{caption}](evidencias-s13/{name})\n')
def link(url,label): return f'<link href="{url}" color="#166d7a">{label}</link>'

p('LENGUAJE DE PROGRAMACIÓN II · SESIÓN 13','H2ES')
p('PharmaSoft<br/>Optimización y preparación<br/>para producción','TitleES')
p('Actividad autónoma · Reto 02','H2ES')
p('Estudiante: Pacho (apellido utilizado en las entregas existentes).<br/>Docente: Benjamin David Reyna Barreto.<br/>Universidad Peruana Unión · Ingeniería de Sistemas · Ciclo IV, 2026-2.')
p('Mediciones: 8 de noviembre de 2026, hora de Lima. Entrega prevista: 11 de noviembre de 2026, 23:59. Los registros JSON usan UTC para conservar trazabilidad.')
h('Resultado observado')
p(f"La carga diferida del diseño autenticado reduce el paquete inicial de {before['bytes']/1000:.2f} a {after['bytes']/1000:.2f} kB: {(1-after['bytes']/before['bytes'])*100:.2f} %. En 20 consultas por catálogo se observaron 19 aciertos y un fallo por caché. La venta de ensayo {trace['saleId']} descontó el stock de 10 a 9.")
p('Los errores incorporan requestId y la SPA muestra su código de seguimiento. Se retiró el DNI completo del log de registro de clientes. Con Redis detenido, la consulta de productos continúa y el health global refleja el modo degradado.')
h('Alcance y límites de la entrega')
p('Este informe conserva mediciones y capturas reales de Oracle, Redis, Nginx y la SPA locales. C-05 detectó que las bajas seguían visibles: se corrigió con un filtro paginado de activas y la opción Mostrar inactivas para conservar el historial. Los seis casos de la matriz quedaron comprobados.')
p('Quedan pendientes los tres commits en días distintos por repositorio, la creación de las solicitudes de incorporación y la carga al aula virtual. No se inventan fechas ni enlaces. El entorno local usa HTTP; las recomendaciones de producción requieren implementación y validación antes de los tres locales.')

page();title('A. Carga diferida y tamaño de entrega')
p('Se ejecutó ng build --stats-json en producción antes y después. El archivo se abrió en esbuild Bundle Size Analyzer. La versión instalada de Angular genera browser-stats.json. Se recorren imports estáticos desde main y se agregan los CSS iniciales; los imports dinámicos se excluyen.')
table(['Medida','Antes','Después'],[
 ['Initial total, bytes',before['bytes'],after['bytes']],
 ['Initial total, kB decimales',f"{before['bytes']/1000:.2f}",f"{after['bytes']/1000:.2f}"],
 ['Transferencia estimada del CLI','88,41 kB','86,32 kB'],
 ['Mejora','MainLayout importado al arrancar','MainLayout con loadComponent tras authGuard']], [175,150,150])
h('Los cinco módulos más pesados del paquete inicial final')
table(['Módulo (metafile)','Aporte','Origen y dependencia'],[
 [n.replace('node_modules/',''),f'{b/1000:.2f} kB',
  'Angular: infraestructura del framework' if '@angular/' in n else 'RxJS: operadores y observables' if 'rxjs' in n else 'Código propio']
 for n,b in after['modules']], [295,65,115])
p('bytesInOutput representa el aporte de cada archivo fuente al paquete emitido; no es el tamaño de descarga comprimido. Las cinco filas no equivalen a cinco features. Los catálogos y ventas siguen en chunks diferidos. No se eliminó funcionalidad ni se sustituyó una biblioteca por otra.')
pic('A-analyzer.png','A-analyzer.png · Captura real del analizador de esbuild con el metafile final.',maxheight=140)

page();title('A. Comparación de precarga')
p('Se comparó la configuración sin precarga con withPreloading(PreloadAllModules). Cinco contextos nuevos por variante; Chrome con caché deshabilitada, 1,5 Mbit/s de descarga, 750 kbit/s de subida y 80 ms de latencia. En ambas se espera 5 s en Inicio tras el login y luego se abre Ventas. Se midió hasta el encabezado y la carga del selector de clientes.')
table(['Variante','Bytes de primera pantalla¹','Clic a Ventas','Login a Ventas²'],[
 [k,f"{v['firstBytes']:.0f} B",f"{v['clickMs']:.2f} ms",f"{v['loginMs']:.2f} ms"] for k,v in summary.items()], [105,145,110,115])
p('¹ Suma de encodedDataLength de Network.loadingFinished desde login hasta el fin de la espera en Inicio; incluye recursos, API y cabeceras de transporte de esa sesión. No es el Initial total del compilador. ² Incluye los 5 s de espera deliberada.','SmallES')
table(['Ensayo','Sin precarga: bytes / clic ms','Con precarga: bytes / clic ms'],[
 [i+1,f"{a['firstBytes']} / {a['ventasAfterClickMs']:.2f}",f"{b['firstBytes']} / {b['ventasAfterClickMs']:.2f}"]
 for i,(a,b) in enumerate(zip(nav['sin-precarga']['trials'],nav['con-precarga']['trials']))], [65,205,205])
delta=summary['con-precarga']['firstBytes']-summary['sin-precarga']['firstBytes']
saved=summary['sin-precarga']['clickMs']-summary['con-precarga']['clickMs']
p(f"Decisión: mantener la carga bajo demanda. La precarga global añade {delta:.0f} bytes ({delta/summary['sin-precarga']['firstBytes']*100:.1f} %) a la primera pantalla y reduce la espera media del clic aproximadamente {saved:.0f} ms. En tres locales con enlaces compartidos conviene evitar descargar módulos que el usuario puede no utilizar. La prioridad cambia si las mediciones reales de caja muestran que esos milisegundos dominan la operación; podría ensayarse precarga selectiva de Ventas.")
p('Las cifras describen este entorno y una carga de ensayo pequeña; no prueban rendimiento de 3 locales concurrentes ni una mejora universal de latencia. La variante de precarga se retiró tras medir.')
pic('A-medicion.png','A-medicion.png · Exportación gráfica de los resultados guardados; no es una captura de DevTools.',maxheight=155)

page();title('B. Políticas de caché del navegador')
p('Nginx sirve la SPA en localhost:8081. Se verificaron los encabezados con curl -I y la recarga con Network del protocolo DevTools de Chrome. Un HTTP 200 de DevTools puede venir de memoria: se registran además requestServedFromCache y fromDiskCache.')
rows=[]
for r in header_rows:
    cc=next((s.split(':',1)[1].strip() for s in r['output'].splitlines() if s.lower().startswith('cache-control:')),'No presente')
    rows.append([r['resource'],cc,'Red / revalidación' if 'index' in r['resource'] else 'Red' if '/api/' in r['resource'] else 'Memoria','Sí'])
table(['Recurso','Cache-Control obtenido','Origen de recarga','Correcto'],rows,[150,190,80,55])
p('La recarga de /ventas sirvió el documento con no-cache y los JS/CSS desde memoria; las llamadas del API fueron a red. La tabla usa el nombre real de cada archivo ensayado. index.html tiene la misma política del fallback de la SPA. No se observó 304 en esta recarga; no se lo presume a partir de no-cache.')
h('Por qué el API no debe guardarse en el navegador')
p('Los catálogos incluyen precio y stock y las respuestas pueden depender del usuario. Reutilizarlas tras ventas, cambios de permisos o cierre de sesión produciría datos obsoletos o exposición de datos. Spring Security añade por defecto Cache-Control: no-cache, no-store, max-age=0, must-revalidate, además de Pragma: no-cache y Expires: 0. No-store evita almacenar; no-cache por sí solo permite almacenar y exige revalidar.')
p('La caché Redis es una capa del servidor: admite TTL e invalidaciones coordinadas y no reemplaza estas restricciones del navegador. Nginx no habilita proxy_cache para /api/.')
pic('B-cabeceras.png','B-cabeceras.png · Salida de encabezados obtenida con curl -I, exportada sin credenciales.',maxheight=240)

page();title('B. Simulación de despliegue')
p('En el mismo contexto del navegador y con la caché conservada se abrió Productos, se cambió el título a «Productos - catálogo actualizado», se ejecutó otro build de producción y se recargó. Nginx continuó en ejecución y su volumen sirvió el directorio reconstruido.')
table(['Observación','Obtenido'],[
 ['Texto visible nuevo',str(deploy['newTextVisible'])],['Se detuvo Nginx','No'],['Se borró la caché del navegador','No'],
 ['JS/CSS con nombres nuevos',str(len(deploy['added']))],
 ['main antes / después',next(n for n in deploy['removed'] if n.startswith('main-'))+' / '+next(n for n in deploy['added'] if n.startswith('main-'))],
 ['CSS y runtime compartido','Conservaron hash cuando su contenido no cambió']], [175,300])
p('El texto cambió el chunk de Productos y propagó nuevos hashes a los archivos que lo referencian, incluido main. index.html revalidado apunta a esa nueva cadena. Los archivos nuevos van a red y los hashes conservados siguen reutilizables. Los nombres completos y los eventos de recarga están en B-despliegue.json. Que aparezcan varios hashes nuevos no significa que se haya descargado todo: la SPA solo solicita el grafo de la ruta visitada.')
pic('B-productos-antes.png','B-productos-antes.png · Recorte de la captura antes de reconstruir.',maxheight=110,crop=(240,80,1360,340))
pic('B-productos-despues.png','B-productos-despues.png · Recorte: mismo navegador y nuevo título.',maxheight=110,crop=(240,80,1360,340))
p('Riesgo del montaje de laboratorio: el build reemplaza dist mientras hay tráfico; una pestaña antigua podría pedir un chunk eliminado. En producción desplegar por releases atómicas, activar index al final y conservar hashes anteriores durante las sesiones abiertas.','SmallES')

page();title('C. Redis: aciertos y tiempos')
p('Se inició la JVM con producción y Redis local. La primera lectura de cada clave fue un fallo; se hicieron 20 GET secuenciales por catálogo. El reinicio de la JVM no elimina Redis: hay que partir de la clave ausente y registrar deltas de métricas si existe otra actividad. Las capturas JSON conservan el estado previo y posterior de cache.gets.')
table(['Caché','Fallos','Aciertos','Tasa','Primer GET','Media de 19 hit'],[
 [n,1,19,'95 %',f"{v['firstMs']:.3f} ms",f"{v['meanHitMs']:.3f} ms"] for n,v in cache.items()], [85,50,55,50,105,130])
p('Tasa = hit / (hit + miss) × 100 = 19 / 20 × 100 = 95 %. Los valores de cache.gets coinciden con 19 hits y 1 miss en cada caché. El ensayo filtró cache y result; también están disponibles las etiquetas name y cache.manager de esta instalación. Para repetición manual usar name:categorias o name:productos y result:hit/miss.')
p('Los tiempos son de extremo a extremo del cliente Node hacia localhost:8080, incluyendo seguridad JWT, carga del usuario y transporte; no son tiempo puro de Oracle. Solo hay un primer fallo por caché: su «media» tiene n=1. No se presenta como un benchmark estadístico de fallos. Los 19 aciertos evitan la consulta del catálogo, aunque el filtro de seguridad todavía puede consultar el usuario.')
h('TTL verificado y restaurado')
table(['Configuración / paso','TTL obtenido','Hora UTC'],[
 ['CACHE_TTL=1m; GET de clave nueva',ttl[0]['ttl'],ttl[0]['at']],
 ['Sin leer la clave durante la espera',ttl[1]['ttl'],ttl[1]['at']],
 ['CACHE_TTL=10m; clave repoblada',ttl[2]['ttl'],ttl[2]['at']]], [205,65,205])
p('Clave del ensayo: categorias::pagina-0-7-nombre-asc. redis-cli TTL devolvió 60; tras más de un minuto, -2 (inexistente); al restaurar y repoblar, 600. La variable cambia entradas nuevas, no las ya guardadas. El filtro final de C-05 añade el sufijo -activas-false/true a las claves paginadas para separar ambas consultas; el procedimiento de reproducción ya utiliza ese sufijo.')
pic('C-aciertos.png','C-aciertos.png · Exportación gráfica de Actuator, tiempos y redis-cli.',maxheight=180)

page();title('C. Matriz de invalidación ejecutada')
table(['ID','Operación / esperado','Obtenido','Resultado'],[
 ['C-01','Crear categoría: aparece','ID '+str(matrix[0]['categoryId'])+' presente en lista','Cumple'],
 ['C-02','Renombrar: producto muestra nombre nuevo',matrix[1]['obtained'],'Cumple'],
 ['C-03','Precio nuevo en detalle y lista','3,75 en ambas respuestas','Cumple'],
 ['C-04','Venta: stock descontado','Stock 10 → 9, venta '+str(trace['saleId']),'Cumple'],
 ['C-05','Eliminar categoría vacía: ya no aparece','Ausente de activas; historial mantiene estado=false','Cumple tras corrección'],
 ['C-06','Redis apagado: funciona y health DOWN','Productos HTTP 200; health HTTP 503 DOWN','Cumple']], [45,150,190,90])
p('Se usaron registros exclusivos de ensayo; el cliente contiene datos sintéticos que no se exportan. La venta se conserva en el historial y no se borró. C-02 y C-04 calientan la lista antes de escribir para comprobar que se invalida una copia previa.')
h('Revisión de las anotaciones')
p('Categoría create/delete invalidan categorias; update invalida categorias y productos porque ProductoResponseDTO contiene categoriaNombre. Producto create/update/delete y Venta.registrar invalidan productos con allEntries=true. La caché envuelve la transacción para invalidar después del commit. No se encontró un defecto de anotación en los casos de ensayo.')
p('Antes: C-05 devolvía HTTP 204 y estado=false, pero findAll conservaba la baja en el listado habitual. La invalidación funcionaba; el defecto era de la vista. Después: soloActivas=true filtra en Oracle antes de paginar y forma parte de la clave de caché. La SPA solicita activas por defecto y Mostrar inactivas conserva la consulta histórica. La API sin el parámetro mantiene su comportamiento anterior y los formularios pueden recuperar la categoría original. La nueva prueba calentó la lista activa, dio de baja otra categoría vacía y comprobó ausencia inmediata y presencia inactiva en historial.')
pic('C-04-stock.png','C-04-stock.png · Recorte del producto de ensayo tras la venta desde la SPA.',maxheight=180,crop=(240,80,1360,450))

page();title('C. Evidencia de la corrección C-05')
p('El filtro se ejecuta en el servidor antes de paginar: no se esconden filas únicamente en la página actual. Las dos variantes tienen claves distintas y las escrituras invalidan todo el catálogo, incluidas las páginas activas e históricas. La baja sigue siendo lógica y no se elimina información de auditoría.')
pic('C-05-activas.png','C-05-activas.png · Vista habitual: la categoría dada de baja ya no aparece.',maxheight=210,crop=(240,80,1360,500))
pic('C-05-historico.png','C-05-historico.png · Mostrar inactivas: la misma categoría permanece para consulta administrativa.',maxheight=210,crop=(240,80,1360,500))
p('C-05-spa.json registra la ausencia por defecto y la presencia en historial; C-matriz.json conserva el resultado anterior y el resultado corregido. Una prueba del proxy real de Spring verifica que la baja invalida la lista activa y que su caché se separa de la administrativa. Dos pruebas de frontend verifican la solicitud paginada y la compatibilidad con el arreglo de la API antigua.')

page();title('C. Redis apagado y riesgos restantes')
p(f"Con Redis detenido: GET /productos devolvió HTTP {down['products']['status']}. Health público devolvió HTTP {down['anonymous']['status']} con status={down['anonymous']['data']['status']}; con administrador también fue DOWN y mostró Redis como componente fallido. Al restaurarlo, health volvió a HTTP {up['anonymous']['status']} UP.")
pic('C-06-redis-detenido.png','C-06-redis-detenido.png · Recorte: la SPA muestra el producto durante la caída.',maxheight=180,crop=(240,80,1360,450))
h('Interpretación')
p('El manejador de errores de caché permite seguir leyendo desde Oracle. Los límites de conexión y operación Redis son de 500 ms cada uno; una petición puede intentar lectura y escritura y sufrir más de un timeout. «Funciona» no equivale a la misma latencia. Los logs registran advertencias sin valores de caché ni credenciales.')
p('Health global DOWN refleja una dependencia degradada; no significa que el proceso esté muerto. Liveness y readiness actuales no garantizan que cada dependencia crítica se evalúe como la operación de venta necesita. Configurar sondas y alertas con este criterio; no reiniciar indefinidamente la API por una caída de Redis.')
h('Riesgos de consistencia que este ensayo no elimina')
p('Si se escribe mientras Redis está caído, la invalidación puede perderse y reaparecer una clave antigua al reconectar. Además, una lectura concurrente iniciada antes del commit puede repoblar un valor viejo después de una invalidación. Un solo Redis compartido evita cachés aisladas por instancia, pero no elimina estas ventanas. Purgar selectivamente al recuperar y diseñar invalidación con versiones/eventos si se requiere consistencia fuerte. El TTL limita la vigencia, no la vuelve instantánea.')
p('La venta descuenta stock con un UPDATE condicional en Oracle dentro de una transacción; no confía en el stock de Redis para autorizar la operación. Falta un ensayo de carga concurrente de los tres locales y de escrituras durante la caída antes de certificar producción.')

page();title('D. Trazabilidad de una venta y errores')
p(f"Se registró desde la SPA la venta {trace['saleId']} por S/ {trace['total']:.2f}. Network entregó X-Request-Id: {trace['requestId']}. La búsqueda con rg de ese valor recuperó tres líneas del log de producción.")
pic('D-venta-log.png','D-venta-log.png · Líneas reales filtradas por el identificador recibido por la SPA.',maxheight=140)
p('La primera línea indica que comenzó el registro y cuántas líneas tiene. La segunda identifica la venta persistida, sin cliente ni DNI. La tercera cierra la petición HTTP: POST /api/v1/ventas, estado 201 y 127 ms. El evento «persistida» ocurre dentro de la transacción; el acceso HTTP 201 es la evidencia de respuesta exitosa posterior. Un log interno aislado no prueba por sí solo que el commit terminó.')
h('requestId en backend y frontend')
p('RequestIdFilter genera ocho caracteres hexadecimales, los coloca en MDC y en X-Request-Id, y limpia el contexto al finalizar. GlobalExceptionHandler incorpora MDC.get("requestId") en ErrorResponseDTO; también se agregó en los errores de filtros 401/403. Se cubrieron errores de formato y fallos no controlados sin devolver detalles internos.')
p('mensajeError de la SPA añade «Código de seguimiento: ...» desde error.error.requestId o, como alternativa, X-Request-Id. CORS ya expone esa cabecera. El usuario puede enviar solo ese código al soporte para localizar la petición sin compartir token, contraseña ni DNI. El código identifica una petición, no toda una sesión; ocho caracteres pueden colisionar, por lo que soporte debe combinarlo con fecha y ruta.')
pic('D-error-requestId.png','D-error-requestId.png · Recorte del error 404 real y su código de seguimiento.',maxheight=150,crop=(240,80,1360,340))

page();title('D. Auditoría y monitoreo')
table(['Búsqueda','Histórico','Ejecución corregida'],[
 [n,v['historico'],v['ejecucion_corregida']] for n,v in audit.items() if isinstance(v,dict)], [290,85,100])
p('Se revisó el archivo de producción y las líneas desde el arranque corregido. La búsqueda de palabras es orientativa: un nombre de clase puede dar falso positivo y un secreto sin etiqueta puede pasar inadvertido. Se añadieron patrones de JWT completos y DNI explícitos y se revisaron los lugares que escriben logs. Los tokens y claves reales usados durante la prueba nunca se exportaron.')
p('Defecto corregido: ClienteServiceImpl.create registraba el DNI completo. Ahora registra «Inicio registrar cliente» y mantiene el ID interno de éxito. No se copian las coincidencias históricas al informe. Corregir el código no borra registros anteriores: restringir su acceso y aplicar la política de retención o redacción aprobada. La auditoría no demuestra que todo el equipo esté libre de secretos; cubre el archivo y los patrones indicados.')
table(['Redis','Sin token','ADMIN con token'],[
 ['Encendido','HTTP 200; UP; sin componentes','HTTP 200; UP; componentes db, redis, disco y sondas'],
 ['Apagado','HTTP 503; DOWN; sin componentes','HTTP 503; DOWN; detalle del fallo Redis']], [90,175,210])
metric=data('D-ventas-metricas.json')['data']; vals={v['statistic']:v['value'] for v in metric['measurements']}
p(f"Métrica http.server.requests filtrada por uri:/api/v1/ventas: COUNT={vals['COUNT']:.0f}; TOTAL_TIME={vals['TOTAL_TIME']:.7f} s; MAX={vals['MAX']:.7f} s. Media=TOTAL_TIME/COUNT={vals['TOTAL_TIME']/vals['COUNT']*1000:.3f} ms. La muestra corresponde a un POST exitoso 201; no se registraron errores en esa serie. No describe /ventas/buscar ni ofrece p95, concurrencia o un SLA. Los valores se reinician con la JVM y el máximo depende de su ventana de registro.")
pic('D-health.png','D-health.png · Exportación de estados reales y conteos de auditoría sin datos sensibles.',maxheight=210)

page();title('E. Arquitectura y configuración')
p('Propuesta para tres locales: navegadores por HTTPS a un Nginx común; Nginx envía /api a PharmaBackend; Java consulta Oracle y Redis privados. Las tres sedes comparten datos y caché. La SPA no implementa ventas offline.')
table(['Pieza','Laboratorio observado','Producción propuesta'],[
 ['Navegadores de 3 locales','HTTP localhost:8081','HTTPS 443 hacia Nginx'],
 ['Nginx','Host 8081 → contenedor 80','443 público; 80 solo redirección'],
 ['PharmaBackend','8080 en anfitrión','8080 privado tras proxy'],
 ['Oracle','Host 1522 → contenedor 1521','1521 privado; no publicar a Internet'],
 ['Redis','127.0.0.1:6379 → 6379','6379 privado, autenticación/TLS si remoto']], [110,180,185])
p('Diagrama incluido en ambos README: Navegadores (locales 1, 2, 3) → Nginx:443 → PharmaBackend:8080 → Oracle:1521 y Redis:6379. Actuator se consulta internamente en 8080, con autorización para detalles y métricas.')
table(['Variable / grupo','Propósito, sin valores reales'],[
 ['SPRING_PROFILES_ACTIVE','prod; evita configuración de desarrollo'],
 ['DB_URL, DB_USERNAME, DB_PASSWORD','Conexión Oracle y cuenta de mínimo privilegio'],
 ['JWT_SECRET','Base64 de 32 bytes aleatorios o más; igual en réplicas'],
 ['JWT_EXPIRACION_MINUTOS','Duración de la sesión (30 min predeterminados en prod)'],
 ['SERVER_PORT','Puerto privado de Java (8080 por defecto)'],
 ['REDIS_HOST, REDIS_PORT','Redis compartido; 6379 por defecto'],
 ['CACHE_TTL','10m normal; 1m solo para el ensayo'],
 ['SPRING_DATA_REDIS_PASSWORD / SSL_ENABLED','ACL y TLS para Redis remoto; prefijo completo SPRING_DATA_REDIS_'],
 ['FRONTEND_ORIGINS','Orígenes HTTPS autorizados por CORS'],
 ['SPRING_FLYWAY_ENABLED','Controlar migraciones sobre un esquema preparado']], [225,250])
p('No hay secretos de backend en Angular. environment.ts contiene /api/v1 y se integra al build. El compose local fija puerto y alias backend:8080; dominio y TLS se definen en Nginx. Valores locales de desarrollo y cuentas de clase heredadas deben retirarse/rotarse antes de compartir la configuración de producción.')

page();title('E. Despliegue, reversión y prioridades')
h('Procedimiento verificable')
p('1. Identificar releases por commit. Guardar JAR, frontend completo y configuración anterior. Respaldar Oracle y comprobar restauración antes de migrar.<br/>2. Backend: Java 21, mvnw clean verify y java -jar con perfil prod y variables seguras. El esquema local preexistente se ensayó con Flyway deshabilitado; V2 de seguridad sola no construye todo el esquema. Preparar migraciones iniciales y validar ddl-auto=validate.<br/>3. Frontend: npm ci y ng build --stats-json. Desplegar hashes primero y activar index.html al final, por directorios de release atómicos. Iniciar Nginx y Redis privados.<br/>4. Validar health público/ADMIN, login, catálogo, venta de ensayo, stock y requestId. Si falla, volver al release anterior y repetir los controles.<br/>5. Reversión: reactivar JAR y frontend anteriores compatibles. Purgar solo claves de catálogo del entorno si cambia la serialización. Restaurar Oracle o usar migración compensatoria cuando haya cambios incompatibles; cambiar el JAR no revierte datos.')
table(['Práctica','Estado','Acción pendiente'],[
 ['Lazy load, @defer y hashes','Cumple','Vigilar presupuestos'],
 ['HTML revalidado y API no-store','Cumple','Conservar política en proxy'],
 ['Redis TTL e invalidación','Parcial','Concurrencia y recuperación tras escrituras en caída'],
 ['Logs, requestId y rotación','Cumple / histórico pendiente','Aplicar retención y acceso a históricos'],
 ['Health y métricas restringidos','Cumple / alertas pendientes','Alertas externas y sondas por criticidad'],
 ['Producción, migraciones y credenciales','Parcial','Completar V1; rotar y retirar cuentas de clase'],
 ['HTTPS y backups restaurables','No en laboratorio','Implementar y ensayar antes del primer local'],
 ['C-05','Cumple tras corrección','Mantener filtro de activas e historial'],
 ['Versionamiento','Pendiente','3 fechas y PR reales']], [165,125,185])
h('Tres recomendaciones priorizadas')
p('<b>P1. HTTPS y red privada:</b> publicar solo Nginx por 443, proteger administración con VPN/red privada y sustituir cuentas de clase por usuarios y secretos gestionados.<br/><b>P1. Oracle recuperable:</b> copias cifradas fuera del servidor y simulacros. Proponer RPO de 1 hora y RTO de 4 horas para decisión de gerencia; son objetivos, no garantías medidas.<br/><b>P2. Redis compartido y alertas:</b> una caché para las instancias de los tres locales, alertas de health/5xx/latencia y procedimiento selectivo de purga tras caída. Definir contingencia por pérdida de Internet; la aplicación actual requiere conexión.')

page();title('F. Entrega, validación y evidencias')
p('Validación ejecutada: frontend, 23 archivos y 53 pruebas aprobadas; backend, 42 pruebas aprobadas y JAR construido. Se excluyó PharmaBackendApplicationTests, que depende del contexto externo; esto no se presenta como una suite completa de contexto. Las comprobaciones HTTP y SPA de este informe sí usaron Oracle, Redis y Nginx reales.')
table(['Entregable / criterio','Estado'],[
 ['Informe A a E y evidencias antes/después','Creado en docs/informe-s13.pdf y copia para aula virtual'],
 ['Mejora adicional y medición inicial','Implementada y medida'],
 ['Precarga, navegador y despliegue','Medidos; se conserva sin precarga'],
 ['Matriz C-01 a C-06','Ejecutada; C-05 corregido y repetido con evidencia'],
 ['requestId en errores y SPA','Implementado, probado y capturado'],
 ['README de ambos repositorios','Actualizados: arquitectura, variables, pasos, reversión y prioridades'],
 ['Tres commits en días distintos por repositorio','Pendiente: no se alteraron fechas'],
 ['Solicitud de incorporación a develop en ambos','Textos preparados; creación remota pendiente'],
 ['Entrega al aula virtual','Archivo listo; subida pendiente del estudiante']], [265,210])
h('Archivos para repetir y sustentar')
p('docs/s13/medir.mjs ejecuta los ensayos con credenciales en variables de entorno. docs/s13/reproducir.md explica condiciones y límites. docs/evidencias-s13 contiene metafiles, JSON de resultados y capturas con prefijos A, B, C y D. Las exportaciones gráficas de tablas están identificadas como tales; no se presentan como capturas de DevTools o Postman.')
p('Las fechas de los tres commits no se pueden cumplir dentro de una sola sesión. Usar fechas reales, revisar los cambios locales previos antes de confirmar, publicar la rama y abrir PR hacia develop en ambos repositorios. No se afirmarían solicitudes creadas sin enlaces verificables.')
h('Referencias y respaldo técnico')
for url,label in [
 ('https://angular.dev/guide/templates/defer','Angular: Deferred loading with @defer'),
 ('https://esbuild.github.io/analyze/','esbuild: Bundle Size Analyzer'),
 ('https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control','MDN: Cache-Control'),
 ('https://docs.spring.io/spring-data/redis/reference/redis/redis-cache.html','Spring Data Redis: Redis Cache'),
 ('https://docs.spring.io/spring-boot/reference/actuator/metrics.html','Spring Boot: Metrics'),
 ('https://docs.spring.io/spring-security/reference/servlet/exploits/headers.html','Spring Security: Security HTTP Response Headers')]:
    p(link(url,label),'SmallES')
p('Fuente académica: Actividad autónoma, sesión 13, documento de seis páginas facilitado por el estudiante. Los datos experimentales proceden del proyecto local; la documentación oficial respalda los conceptos, no sustituye las mediciones.','SmallES')

def decorate(canvas,doc):
    canvas.saveState();canvas.setStrokeColor(colors.HexColor('#d8e4ed'));canvas.line(48,802,547,802)
    canvas.setFont('Arial',8);canvas.setFillColor(colors.HexColor('#526477'))
    canvas.drawString(48,814,'PharmaSoft | Actividad autónoma S13 | Pacho')
    canvas.drawString(48,30,'Evidencias locales · 08/11/2026 · Lima');canvas.drawRightString(547,30,f'{doc.page}')
    canvas.restoreState()

pdf=DOCS/'informe-s13.pdf'
SimpleDocTemplate(str(pdf),pagesize=(595.28,841.89),rightMargin=60,leftMargin=60,topMargin=62,bottomMargin=52,
    title='PharmaSoft - Informe de optimización y preparación para producción S13',author='Pacho').build(story,onFirstPage=decorate,onLaterPages=decorate)
shutil.copy2(pdf,DOCS/'Pacho_LP2_S13_Autonoma.pdf')
(DOCS/'informe-s13.md').write_text('\n'.join(md),encoding='utf-8')
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in E.iterdir() if p.is_file() and p.name!='manifest-sha256.json'}
write('manifest-sha256.json',manifest)
print('Informe PDF, copia para aula virtual, fuente editable y manifiesto generados.')
