"""Arma el informe editable a partir de las mediciones y capturas conservadas."""

from collections import Counter
from pathlib import Path
import hashlib
import json
import re

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from PIL import Image

DOCS = Path(__file__).resolve().parents[1]
ROOT = DOCS.parents[1]
OLD = DOCS / 'evidencias-s13'
ROUND = DOCS / 'evidencias-s13-autonoma-manual/2026-11-08-control-pc'
PART_F = DOCS / 'evidencias-s13-autonoma-manual/2026-11-08-parte-f'
REFERENCE = ROOT / 'pharma-frontend/docs/Pacho_LP2_S13_Practica_Editable.docx'
REFERENCE_HASH = 'b59d1341619b62ddf8527acf920facef21716b66dd74285b2b17c57d623e92e8'
assert hashlib.sha256(REFERENCE.read_bytes()).hexdigest() == REFERENCE_HASH


def load(name, folder=ROUND):
    return json.loads((folder / name).read_text(encoding='utf-8-sig'))


def initial(name):
    outputs = load(name)['outputs']
    queue = [key for key, value in outputs.items() if value.get('entryPoint') == 'src/main.ts']
    visited = {key for key in outputs if key.startswith('styles-') and key.endswith('.css')}
    while queue:
        key = queue.pop()
        if key in visited:
            continue
        visited.add(key)
        queue.extend(item['path'] for item in outputs[key]['imports']
                     if item['kind'] != 'dynamic-import' and item['path'] in outputs)
    sizes = Counter()
    for key in visited:
        for module, value in outputs[key]['inputs'].items():
            sizes[module] += value['bytesInOutput']
    return sum(outputs[key]['bytes'] for key in visited), sizes.most_common(5)


def decimal(value, places=2):
    return f'{value:.{places}f}'.replace('.', ',')


def kib_bytes(value):
    return f'{value:,}'.replace(',', ' ')


def as_code(value):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(value)
    r.font.name = 'Consolas'
    r.font.size = Pt(8.5)
    return p


def para(value='', style=None):
    return doc.add_paragraph(value, style=style)


def label(title, value):
    p = doc.add_paragraph()
    p.add_run(title + '. ').bold = True
    p.add_run(value)
    return p


def page(title):
    doc.add_page_break()
    para(title, 'Heading 1')


def table(headers, rows, widths):
    t = doc.add_table(rows=0, cols=len(headers))
    t.autofit = False
    for c, width in zip(t.columns, widths):
        c.width = Cm(width)
    for n, values in enumerate([headers, *rows]):
        row = t.add_row()
        props = row._tr.get_or_add_trPr()
        props.append(OxmlElement('w:cantSplit'))
        if n == 0:
            props.append(OxmlElement('w:tblHeader'))
        for cell, value, width in zip(row.cells, values, widths):
            cell.width = Cm(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            prop = cell._tc.get_or_add_tcPr()
            shade = OxmlElement('w:shd')
            shade.set(qn('w:fill'), 'E2EAF2' if n == 0 else 'F5F7FA' if n % 2 == 0 else 'FFFFFF')
            prop.append(shade)
            borders = OxmlElement('w:tcBorders')
            for side in ('top', 'left', 'bottom', 'right'):
                border = OxmlElement('w:' + side)
                for k, v in {'val': 'single', 'sz': '4', 'color': 'D9D9D9'}.items():
                    border.set(qn('w:' + k), v)
                borders.append(border)
            prop.append(borders)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(str(value))
            r.bold = n == 0
            r.font.size = Pt(9)
    para()


figure_number = 0


def figure(name, caption, folder=ROUND, height=10, crop_bottom=None):
    global figure_number
    file = folder / name
    with Image.open(file) as bitmap:
        w, h = bitmap.size
    crop_bottom = crop_bottom or h
    picture_height = min(height, 17 * crop_bottom / w)
    picture_width = picture_height * w / crop_bottom
    figure_number += 1
    p = para(f'Figura {figure_number:02d}. {caption}', 'Caption')
    p.paragraph_format.keep_with_next = True
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    shape = p.add_run().add_picture(str(file), width=Cm(picture_width), height=Cm(picture_height))
    if crop_bottom < h:
        fill = shape._inline.xpath('.//pic:blipFill')[0]
        source = OxmlElement('a:srcRect')
        source.set('b', str(round(100000 * (1 - crop_bottom / h))))
        fill.insert(1, source)
    description = shape._inline.docPr
    description.set('descr', caption)


doc = Document(REFERENCE)
body = doc._element.body
for child in list(body):
    if child.tag != qn('w:sectPr'):
        body.remove(child)
for key, rel in list(doc.part.rels.items()):
    if rel.reltype.endswith('/image'):
        del doc.part.rels[key]
footer = doc.sections[0].footer.paragraphs[0]
footer.clear()
footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('Sesión 13 autónoma  |  Página ').font.size = Pt(8)
field = OxmlElement('w:fldSimple')
field.set(qn('w:instr'), 'PAGE')
footer._p.append(field)
doc.core_properties.title = 'Optimización y preparación para producción de PharmaSoft'
doc.core_properties.subject = 'Actividad autónoma de la sesión 13 con evidencias de ejecución'
doc.core_properties.author = 'Brandon Erly Pacho Mamani'
doc.core_properties.comments = ''

before, _ = initial('A02-stats-antes.json')
after, top = initial('A02-stats-despues.json')
ui = load('ronda-ui.json')
cache = load('C01-C02-series-20.json')['caches']
trace = load('D01-identificadores.json')
errors = load('D02-errores-api.json')
health_on = load('C09-health-on.json')
health_off = load('C09-health-off.json')
health_transition = load('C09-health-on-transicion.json')
ttl = [load(f'C03-ttl-{phase}.json')['ttl'] for phase in ('inicial', 'expirada', 'restaurada')]
deployment = load('B-despliegue.json', OLD)
navigation = load('A-resumen.json', OLD)['navigation']
api_matrix = load('C-matriz-api.json')
test_runs = load('F-pruebas-ronda.json')
assert before > after and [c['hits'] for c in cache.values()] == [19, 19]
assert [c['misses'] for c in cache.values()] == [1, 1]
assert 0 < ttl[0] <= 60 and ttl[1] == -2 and 590 <= ttl[2] <= 600
assert health_off['productos']['status'] == 200 and health_off['publico']['status'] == 503
assert health_on['publico']['data']['status'] == 'UP'
assert api_matrix['bajaAusenteDeActivas'] and api_matrix['bajaHistorico']['data']['estado'] is False
assert api_matrix['producto']['data']['stock'] == 9 and api_matrix['productoLista']['precio'] == 3.75

para('Optimización y preparación para producción de PharmaSoft', 'Title')
para('Informe de la actividad autónoma de la sesión 13', 'Subtitle')
label('Estudiante', 'Brandon Erly Pacho Mamani')
label('Curso', 'Lenguaje de Programación II')
label('Proyectos', 'PharmaBackend y pharma-frontend')
label('Rama', 'feature/optimizacion-produccion-pacho')
label('Fecha de mediciones', '8 de noviembre de 2026, hora de Lima')
para('El informe reúne las comprobaciones del Reto 02 con la estructura de la práctica de S13. Cada ficha incluye procedimiento, resultado, estado y evidencias. Las mediciones de navegador provienen de dos rondas del mismo entorno local. La ronda inicial registró precarga, recarga y despliegue. La ronda en Edge instalado confirmó el analizador, la matriz de catálogos, la venta y los códigos de seguimiento.')
para('Resumen de resultados', 'Heading 1')
table(['Comprobación', 'Resultado observado'], [
    ('Tamaño inicial', f'{decimal(before / 1000)} a {decimal(after / 1000)} kB. Reducción de {decimal(100 * (before - after) / before)} %.'),
    ('Redis', '19 aciertos y 1 fallo de 20 consultas en cada catálogo. TTL de ensayo expirado y restaurado a 10 minutos.'),
    ('Venta e invalidación', f'Venta de ensayo {ui["ventaId"]}. Stock del producto {ui["productoId"]} de 10 a 9. Seis casos de matriz verificados.'),
    ('Seguimiento y salud', f'La venta se correlaciona con el identificador {trace["requestId"]}. Redis detenido deja health en 503 y productos en 200.'),
    ('Entrega', 'Informe y evidencias locales listos. El historial de tres fechas, los PR y la subida al aula se controlan en la parte F.'),
], [5, 12])
label('Entorno', 'Windows, Edge y Postman instalados, Java 21, Oracle local, Redis 7 y Nginx en Docker Desktop. Nginx sirve la SPA en 8081 y la API responde en 8080.')

page('A01 Analizador y módulos iniciales')
label('Procedimiento', 'Compilé Angular en producción con estadísticas e importé browser-stats.json en esbuild Bundle Size Analyzer desde Edge. Identifiqué los archivos iniciales del CLI y sumé bytesInOutput de sus imports estáticos. El gráfico general incluye también salidas diferidas.')
table(['Archivo fuente', 'Aporte inicial', 'Origen'], [(m.replace('node_modules/', ''), f'{kib_bytes(n)} B', 'Angular') for m, n in top], [10, 3.2, 3.8])
label('Resultado observado', 'Los cinco mayores aportes corresponden a Angular Core, Router y Common. La unidad visual del analizador usa escala binaria. La tabla presenta bytes exactos del metafile.')
figure('AA-A01-03-analyzer-general.jpg', 'Metafile final en el analizador de esbuild abierto en Edge.', height=11)
label('Estado', 'Conforme. Los detalles de cada módulo se conservan en AA-A01-04 a AA-A01-08.')

page('A02 Comparación de tamaño antes y después')
label('Procedimiento', 'Compilé dos veces con el mismo código y configuración de producción. Para el antes cargué MainLayout con un import estático. Para el después restauré loadComponent en la ruta protegida. Las salidas fueron a directorios de ensayo separados y la versión servida quedó intacta.')
table(['Medida', 'Antes', 'Después'], [
    ('Bytes iniciales', kib_bytes(before), kib_bytes(after)),
    ('Tamaño inicial', f'{decimal(before/1000)} kB', f'{decimal(after/1000)} kB'),
    ('Transferencia estimada del CLI', '88,40 kB', '86,32 kB'),
    ('MainLayout', 'Incluido al inicio', 'Chunk diferido'),
], [7, 5, 5])
label('Resultado observado', f'Se redujeron {kib_bytes(before-after)} bytes ({decimal(100*(before-after)/before)} %). La transferencia estimada del CLI se registra aparte. La comprobación en Edge abrió Inicio, Categorías, Productos y Ventas.')
label('Evidencias', 'A02-build-antes.txt, A02-build-despues.txt y sus metafiles. A01-build-final.txt contiene los chunks servidos en la ronda Edge.')
figure('H01-login-correcto-despues.jpg', 'Inicio en Edge después de arrancar el backend en perfil prod.', height=9)
label('Estado', 'Conforme.')

page('A03 Precarga de rutas')
label('Procedimiento', 'La primera ronda comparó cinco contextos limpios por variante, con caché deshabilitada, 1,5 Mbit/s de bajada, 750 kbit/s de subida, 80 ms de latencia y una espera fija de 5 s tras el login. La medida hasta Ventas exigió el encabezado y el selector de clientes listo.')
table(['Configuración', 'Primera pantalla', 'Clic a Ventas', 'Login a Ventas'], [
    (key, f'{kib_bytes(round(value["firstBytes"]))} B', f'{decimal(value["clickMs"])} ms', f'{decimal(value["loginMs"])} ms')
    for key, value in navigation.items()
], [4, 4.2, 4.2, 4.6])
label('Decisión', 'Se mantiene la descarga bajo demanda. La precarga transfirió 50 637 bytes adicionales durante la primera pantalla y redujo unos 489 ms entre el clic y la vista de Ventas. Para los tres locales, el ahorro de tráfico inicial justifica conservar la configuración actual. Se puede reevaluar con datos de uso de caja.')
figure('A-medicion.png', 'Resumen de datos capturados por Chrome durante la primera ronda.', OLD, height=6)
label('Evidencias', 'A-sin-precarga.json y A-con-precarga.json contienen las cinco observaciones de cada variante. La cifra de login incluye la espera deliberada.')
label('Estado', 'Conforme en la ronda de medición original.')

page('B01 y B02 Cabeceras y origen en recarga')
label('Procedimiento', 'Verifiqué los cinco recursos por HEAD con curl en Nginx. Para categorías usé una petición autenticada. Los orígenes corresponden a una recarga anterior registrada mediante el protocolo de DevTools. Los nombres con hash pertenecen a cada compilación.')
header_rows = load('B01-cabeceras-curl.json')
table(['Recurso comprobado', 'Cache-Control', 'Origen en recarga'], [
    (entry['ruta'], re.search(r'^Cache-Control:\s*([^\r\n]+)', entry['salidaCurl'], re.I|re.M).group(1),
     ['Red y revalidación', 'Memoria', 'Memoria', 'Memoria', 'Red'][index])
    for index, entry in enumerate(header_rows)
], [6.1, 7.5, 3.4])
label('Resultado observado', 'HTML con no-cache para revalidación. JS y CSS con hash reutilizados desde memoria en la recarga. El API conserva no-store, Pragma no-cache y Expires 0. Guardar respuestas autenticadas del API en el navegador podría exponer datos o mostrar precios y stock obsoletos.')
figure('B-cabeceras.png', 'Cabeceras del ensayo original con curl. La ronda final conserva sus cinco respuestas en B01-cabeceras-curl.json.', OLD, height=8.6)
label('Estado', 'Conforme. B-recarga.json registra red, memoria y disco con los indicadores de DevTools.')

page('B03 Despliegue con Nginx activo')
old_main = next(name for name in deployment['removed'] if name.startswith('main-'))
new_main = next(name for name in deployment['added'] if name.startswith('main-'))
label('Procedimiento', 'En la primera ronda conservé la pestaña de Productos, cambié el título visible y reconstruí la SPA en el volumen que Nginx ya estaba sirviendo. Recargué la misma pestaña sin vaciar su caché.')
label('Resultado observado', f'El título nuevo apareció. Cambiaron {len(deployment["added"])} nombres de archivos y main pasó de {old_main} a {new_main}. styles-AAJM6OEI.css conservó su nombre. B-despliegue.json identifica los archivos que el navegador solicitó y los que reutilizó. El HTML revalidado refirió la nueva cadena de archivos.')
figure('B-productos-antes.png', 'Productos antes de reconstruir la SPA.', OLD, height=6, crop_bottom=440)
figure('B-productos-despues.png', 'Nuevo título en el mismo navegador después de recargar.', OLD, height=6, crop_bottom=440)
label('Estado', 'Conforme en la ronda original. En producción se recomienda activar la versión en forma atómica y conservar los chunks antiguos durante sesiones abiertas.')

page('C01 a C03 Aciertos tiempos y expiración')
label('Procedimiento', 'Eliminé únicamente la clave de ensayo de cada catálogo. Registré contadores hit y miss antes y después de 20 GET secuenciales con los mismos parámetros. El cliente HTTP midió el tiempo total de cada petición y el resultado se calculó con deltas de Actuator.')
table(['Caché', 'Aciertos', 'Fallos', 'Tasa', 'Primer GET', 'Media de 19 aciertos'], [
    (name, values['hits'], values['misses'], f'{decimal(values["rate"],0)} %', f'{decimal(values["firstMs"],3)} ms', f'{decimal(values["meanHitMs"],3)} ms')
    for name, values in cache.items()
], [3.5, 2.2, 2.0, 2.0, 3.3, 4.0])
label('Interpretación', '19 / (19 + 1) da 95 %. La primera consulta es una observación única del fallo. Los tiempos incluyen autorización, transporte y procesamiento. Redis evita consultar el catálogo en Oracle cuando hay acierto.')
table(['Configuración y acción', 'TTL observado'], [
    ('CACHE_TTL=1m y una consulta de la clave nueva', f'{ttl[0]} segundos'),
    ('Después de 64 s sin volver a consultar la clave', f'{ttl[1]} (clave inexistente)'),
    ('CACHE_TTL=10m y consulta posterior al reinicio', f'{ttl[2]} segundos'),
], [11, 6])
label('Evidencias', 'C01-C02-series-20.json conserva las 40 consultas y contadores filtrados. C03-ttl-inicial.json, C03-ttl-expirada.json y C03-ttl-restaurada.json conservan hora, clave y salida numérica de redis-cli.')
figure('C-aciertos.png', 'Registro visual de la primera ronda. Los tiempos de la tabla corresponden a la repetición final.', OLD, height=6)
label('Estado', 'Conforme. El backend quedó con TTL de 10 minutos.')

page('C Matriz de invalidación')
table(['Caso', 'Operación', 'Resultado observado', 'Estado'], [
    ('C-01', 'Crear categoría', f'La categoría {ui["categoriaId"]} apareció en la misma lista activa.', 'Conforme'),
    ('C-02', 'Renombrar categoría', 'El producto mostró el nombre nuevo inmediatamente.', 'Conforme'),
    ('C-03', 'Editar precio', 'S/ 2,50 a S/ 3,75 en lista y detalle.', 'Conforme'),
    ('C-04', 'Registrar venta', f'Venta {ui["ventaId"]} desde la SPA. Stock 10 a 9.', 'Conforme'),
    ('C-05', 'Dar de baja categoría vacía', f'La categoría {ui["vaciaId"]} desapareció de activas. El historial conserva Inactivo.', 'Conforme tras corrección'),
    ('C-06', 'Detener Redis', 'Productos 200 y health 503. Recuperación a UP.', 'Conforme'),
], [2.1, 4.2, 7.5, 3.2])
label('Procedimiento', 'Consulté las listas antes de escribir y repetí los mismos filtros tras cada operación. Usé registros de ensayo y verifiqué precio y stock del mismo producto. La baja conserva un registro de historial y la vista habitual filtra en el servidor antes de paginar.')
label('Hallazgo C-05', 'La versión anterior mostraba las categorías inactivas en la lista habitual. Se agregó soloActivas a la consulta y a su clave de caché. La SPA activa ese filtro al abrir Categorías y permite consultar el historial con Mostrar inactivas.')
figure('AA-C04-01-lista-completa-antes.jpg', 'C-01. Lista activa antes de crear la categoría de ensayo.', height=5.2, crop_bottom=390)
figure('AA-C04-03-lista-despues.jpg', 'C-01. La categoría 147 aparece tras la creación.', height=5.2, crop_bottom=410)

page('C Evidencias de renombrado y edición')
label('C-02 observado', f'La fila del producto {ui["productoId"]} pasó de {ui["marca"]} a {ui["marcaNueva"]} en la columna Categoría.')
figure('AA-C05-01-producto-antes.jpg', 'C-02. Columna Categoría antes de renombrar.', height=5, crop_bottom=425)
figure('AA-C05-03-producto-despues.jpg', 'C-02. La misma fila muestra el nombre de categoría nuevo.', height=5, crop_bottom=425)
label('C-03 observado', 'La edición y el GET de detalle devuelven 3,75. La lista muestra el mismo precio. La captura anterior de C-02 muestra 2,50 y sirve como línea base de la lista.')
figure('AA-C06-05-lista-despues.jpg', 'C-03. Precio actualizado en la lista, con stock inicial de 10.', height=5, crop_bottom=425)
label('Evidencias adicionales', 'AA-C06-01, AA-C06-03 y AA-C06-04 muestran el formulario de detalle antes, al editar y después. C-matriz-api.json registra detalle y lista.')

page('C Evidencias de venta y stock')
label('Procedimiento', f'Vendí una unidad del producto {ui["productoId"]} a un cliente ficticio mediante el formulario de Edge. Dejé la venta de ensayo en el historial. Comparé la misma fila de Productos antes y después.')
figure('AA-C07-02-revision-venta.jpg', 'C-04. Revisión de una unidad con total de S/ 3,75.', height=6)
figure('AA-C07-03-comprobante-tabla.jpg', 'C-04. Detalle del comprobante de la venta de ensayo.', height=4.5)
figure('AA-C07-04-stock-despues.jpg', 'C-04. El mismo producto queda con 9 unidades tras la venta 141.', height=6, crop_bottom=425)
label('Estado', 'Conforme. La figura de precio anterior muestra 10 unidades y C-matriz-api.json confirma el stock posterior.')

page('C Evidencias de baja y recuperación')
figure('AA-C08-01-activa-antes.jpg', 'C-05. Categoría vacía activa antes de la baja.', height=4.6, crop_bottom=425)
figure('AA-C08-03-activa-despues.jpg', 'C-05. La búsqueda queda sin coincidencias en activas.', height=4.6, crop_bottom=425)
figure('AA-C08-04-inactivas.jpg', 'C-05. Mostrar inactivas permite consultar la misma categoría.', height=4.6, crop_bottom=425)
label('C-06 observado', f'Con Redis detenido, productos respondió {health_off["productos"]["status"]} y health {health_off["publico"]["status"]}. El primer sondeo posterior a PONG seguía en {health_transition["publico"]["data"]["status"]}. El sondeo posterior confirmó UP. La reconexión de la aplicación se comprobó de forma independiente del ping de Redis.')
label('Estado', 'Conforme. En D04 se conservan los cuatro estados de health y la evidencia de continuidad.')

page('D01 Trazabilidad de la venta')
label('Procedimiento', 'Registré la venta desde Edge y encontré el identificador del POST con el ID interno de venta. Filtré el log de producción por ese identificador y conservé las tres líneas. La primera ronda también registró X-Request-Id directamente en la respuesta de la SPA para su venta de ensayo.')
for line in (ROUND / 'D01-traza-venta.txt').read_text(encoding='utf-8').splitlines():
    as_code(line)
table(['Línea', 'Interpretación'], [
    ('Inicio registrar venta', 'Comienza el procesamiento de una línea de venta.'),
    ('Venta persistida', f'Oracle asignó el ID {ui["ventaId"]}. El evento se registra dentro de la transacción.'),
    ('POST 201', 'La petición terminó con creación exitosa. El filtro registró 349 ms.'),
], [6.3, 10.7])
label('Evidencia de cabecera', 'D-venta-spa.json de la primera ronda conserva el código 201 y su X-Request-Id. D01-identificadores.json y D01-traza-venta.txt corresponden a la venta 141 de Edge. Cada venta conserva su propio identificador.')
label('Estado', 'Conforme con la evidencia conjunta de ambas rondas.')

page('D02 Errores con código de seguimiento')
table(['Prueba', 'HTTP', 'requestId del cuerpo', 'Coincide con la cabecera'], [
    (case, result['status'], result['data'].get('requestId', 'ausente'),
     'Sí' if result['data'].get('requestId') == result['requestId'] else 'No')
    for case, result in errors.items()
], [5, 2.1, 4.7, 5.2])
label('Resultado en Edge', load('D02-error-spa.json')['mensaje'])
figure('AA-D02-03-error-spa.jpg', 'Error de producto inexistente y código de seguimiento en la interfaz.', height=6, crop_bottom=375)
label('Implementación', 'RequestIdFilter genera el identificador y lo coloca en la cabecera y en el contexto de log. GlobalExceptionHandler lo agrega al cuerpo y los filtros de seguridad lo devuelven para errores de acceso. La SPA usa el cuerpo y, como alternativa, la cabecera.')
label('Incidencia de despliegue', 'Nginx resolvía el alias host-gateway con una IPv6 inalcanzable y podía devolver 502. Cambié el destino local a host.docker.internal en Docker Desktop, validé nginx -t y recargué. Ocho peticiones seguidas alcanzaron la API y devolvieron 401 sin token. La repetición autenticada en Edge mostró el 404 esperado.')
label('Estado', 'Conforme después de corregir la ruta del proxy local.')

page('D03 Auditoría del log de producción')
audit = load('D03-auditoria.json')
signing_key_audit = load('D03-clave-jwt.json')
key_matches = sum(item['coincidencias'] for item in signing_key_audit['archivos'])
assert signing_key_audit['health'] == 'UP' and key_matches == 0
label('Procedimiento', f'Audité {audit["lineasRonda"]} líneas de la ronda de producción y busqué patrones de credenciales y DNI. Comprobé también la contraseña de ensayo en memoria y guardé solo el conteo.')
table(['Comprobación', 'Coincidencias'], [
    ('Palabras password, Bearer o secret', audit['conteos']['palabras']),
    ('Patrón de JWT completo', audit['conteos']['jwt']),
    ('DNI explícito completo', audit['conteos']['dni']),
    ('Contraseña ADMIN de ensayo', audit['contrasenaDeEnsayo']),
    ('Clave de firma del arranque auditado', key_matches),
], [12, 5])
label('Hallazgo y corrección', 'ClienteServiceImpl escribía el DNI completo al registrar un cliente. El evento de inicio ahora omite ese dato y el evento de éxito conserva el identificador interno. Los logs históricos requieren retención y acceso restringido.')
label('Clave JWT', f'En un nuevo arranque con perfil prod y TTL de 10 minutos, busqué la clave de firma exacta directamente en memoria. El backend llegó a UP y se revisaron tres archivos de registro, con {sum(item["lineas"] for item in signing_key_audit["archivos"])} líneas en total.')
label('Estado', 'Conforme en el alcance registrado en D03-auditoria.json y D03-clave-jwt.json. Ambos archivos guardan únicamente los conteos de coincidencias.')

page('D04 Salud del sistema y métricas de ventas')
table(['Redis', 'Sin token', 'Con ADMIN', 'API Productos'], [
    ('Encendido', '200 UP, sin componentes', '200 UP, db y redis UP', '200'),
    ('Apagado', '503 DOWN, sin componentes', '503 DOWN, redis DOWN', '200'),
    ('Restaurado', '200 UP tras reconectar', '200 UP, redis UP', '200'),
], [3, 4.7, 5.6, 3.7])
metrics = load('D04-metricas-ventas.json')['uri']['data']
measure = {row['statistic']: row['value'] for row in metrics['measurements']}
label('Métrica filtrada por uri /api/v1/ventas', f'COUNT={int(measure["COUNT"])}. TOTAL_TIME={decimal(measure["TOTAL_TIME"],7)} s. Media={decimal(1000*measure["TOTAL_TIME"]/measure["COUNT"],3)} ms. MAX de la ventana={decimal(1000*measure["MAX"],3)} ms. La muestra reúne el POST exitoso 201 y el rechazo 409 por stock insuficiente.')
label('Interpretación', 'La respuesta de salud global se degrada si Redis falla, mientras productos puede seguir consultando Oracle. El máximo de Actuator corresponde a la ventana del medidor y puede haber caducado la observación más lenta. El promedio es descriptivo de dos solicitudes.')
figure('C-06-redis-detenido.png', 'Productos en la SPA durante la caída de Redis, captura de la ronda original.', OLD, height=5.8, crop_bottom=405)
figure('AA-00-02-health-inicial.png', 'Consulta pública de salud en Postman, con Redis activo.', height=5, crop_bottom=410)
label('Evidencias', 'C09-health-off.json, C09-health-on-transicion.json, C09-health-on.json y D04-metricas-ventas.json.')
label('Estado', 'Conforme.')

page('E Despliegue en producción')
para('Los tres locales acceden al mismo Nginx. PharmaBackend consulta Oracle para los datos y Redis para los catálogos. En producción se propone exponer Nginx por HTTPS y mantener las dependencias en la red privada.')
as_code('Navegadores de tres locales → Nginx HTTPS 443 → PharmaBackend 8080\n'
        '                                               ├─ Oracle 1521\n'
        '                                               └─ Redis 6379')
table(['Servicio', 'Laboratorio', 'Producción propuesta'], [
    ('Nginx', 'Host 8081 → contenedor 80', '443 público y 80 para redirección'),
    ('PharmaBackend', '8080', '8080 privado'),
    ('Oracle', 'Host 1522 → contenedor 1521', '1521 privado'),
    ('Redis', '127.0.0.1:6379', '6379 privado y compartido'),
], [4, 6.5, 6.5])
table(['Configuración', 'Variables y propósito'], [
    ('Backend y Oracle', 'SPRING_PROFILES_ACTIVE, SERVER_PORT, DB_URL, DB_USERNAME y DB_PASSWORD seleccionan perfil, puerto y conexión.'),
    ('Autenticación y orígenes', 'JWT_SECRET, JWT_EXPIRACION_MINUTOS y FRONTEND_ORIGINS definen firma, vigencia y orígenes permitidos.'),
    ('Redis y migraciones', 'REDIS_HOST, REDIS_PORT, CACHE_TTL, opciones SPRING_DATA_REDIS_* y SPRING_FLYWAY_ENABLED configuran caché y esquema.'),
], [5, 12])
label('Construcción y reversión', 'Compilar y validar el JAR con Java 21 y el frontend con npm. Respaldar Oracle antes de migrar. Publicar artefactos versionados y activar index.html cuando sus hashes estén disponibles. Probar login, salud, catálogo y venta. Si falla, reactivar JAR y SPA compatibles y aplicar la reversión de datos prevista para la migración.')
label('Evidencia', 'La sección Despliegue en producción de ambos README contiene el diagrama y el procedimiento completo.')

page('E Estado de prácticas y recomendaciones')
table(['Práctica', 'Estado', 'Acción'], [
    ('Carga diferida y tamaños', 'Cumple', 'Vigilar presupuesto de entrega en nuevos cambios.'),
    ('HTML revalidado y JS/CSS con hash', 'Cumple', 'Conservar hashes de la versión anterior durante las sesiones.'),
    ('Cache-Control del API', 'Cumple', 'Conservar no-store al desplegar el proxy.'),
    ('TTL, invalidación y contingencia Redis', 'Parcial', 'Tratar escrituras durante la caída y concurrencia de repoblación.'),
    ('Logs y Actuator', 'Cumple en laboratorio', 'Centralizar logs y configurar alertas de producción.'),
    ('TLS y restauración de Oracle', 'Pendiente', 'Configurar HTTPS y ensayar recuperación antes de abrir los locales.'),
], [6, 4.4, 6.6])
label('Prioridad 1', 'Habilitar HTTPS en Nginx, proteger API y bases en red privada y usar cuentas de producción con privilegios acotados.')
label('Prioridad 2', 'Programar copias cifradas de Oracle y ensayar restauración. Medir el tiempo real de recuperación antes de definir un compromiso para los locales.')
label('Prioridad 3', 'Compartir Redis entre instancias y alertar ante health degradado, errores y latencia. Documentar la purga selectiva de claves afectadas por escrituras durante una caída.')

page('F01 Verificación de los commits de entrega')
part_f = load('F-resumen.json', PART_F)
smoke = load('F01-http-nginx.json', PART_F)
frontend = part_f['frontend']
backend = part_f['backend']
label('Procedimiento', 'Exporté los archivos registrados de cada rama a carpetas independientes con git archive. En frontend reutilicé las dependencias instaladas. En backend ejecuté Maven con perfil prod, Oracle y Redis locales, Flyway deshabilitado y validación del esquema.')
table(['Versión evaluada', 'Comprobación', 'Resultado'], [
    (f'Frontend {frontend["antes"]}', 'npm test en copia del commit', '43 aprobadas, 2 fallidas de 45'),
    (f'Frontend {frontend["despues"]}', 'Repetición tras corregir las dos pruebas', '45 aprobadas, 0 fallidas'),
    (f'Backend {backend["commit"]}', 'Suite completa de Maven, incluida la prueba de contexto', '43 aprobadas, 0 fallos, 0 errores y 0 omitidas'),
], [4.5, 6.5, 6])
label('Hallazgo y corrección', 'Las pruebas de Inicio y CategoriaForm fallaban al crear el componente porque su entorno no ofrecía ActivatedRoute. Incorporé provideRouter([]) a ambos módulos de prueba. El commit conserva las 45 pruebas y la repetición completa aprobó las dos que habían fallado.')
label('Alcance', f'La ronda anterior obtuvo {test_runs["frontend"]["tests"]} pruebas aprobadas en el directorio de trabajo. F01 valida los archivos registrados en la rama y su compilación registró {frontend["tamanoInicial"].replace(".", ",")} de tamaño inicial. Angular conservó un aviso de 724 bytes sobre el presupuesto de CSS del formulario de venta.')
table(['Comprobación HTTP', 'Resultado observado'], [
    ('Ruta /ventas', f'{smoke["rutaVentas"]["status"]} · HTML · no-cache'),
    ('Archivo JS inicial', f'{smoke["archivoInicial"]["status"]} · nombre con hash · immutable'),
    ('API de categorías sin sesión', f'{smoke["apiSinToken"]["status"]} · requestId {smoke["requestIdEnCuerpo"]} coincide en cabecera y cuerpo'),
    ('Salud del backend', f'{smoke["saludBackend"]["status"]} · {smoke["estadoSalud"]}'),
], [7, 10])
label('Evidencias', 'La compilación del commit se sirvió en un Nginx temporal en localhost:18081 y se verificó con curl. La carpeta de la parte F contiene las tres salidas de pruebas, la compilación y F01-http-nginx.json.')
chrome = PART_F / 'AA-F01-03-red-chrome.png'
if chrome.is_file():
    page('F01 Captura de la pestaña Red en Chrome')
    label('Procedimiento', 'Abrí la ruta de Ventas en Chrome instalado. Revisé las peticiones del documento y sus recursos en la pestaña Red de DevTools.')
    figure(chrome.name, 'Pestaña Red de Chrome durante la verificación de PharmaSoft.', PART_F, height=17)
else:
    label('Captura de navegador', 'Pendiente de adjuntar la pestaña Red de Chrome. La tabla conserva la verificación de transporte ejecutada sobre el entorno aislado.')

page('F02 Estado de versionamiento y entrega')
histories = part_f['historial']
table(['Repositorio', 'Fechas de la rama S13', 'Ramas en el remoto al verificar'], [
    ('PharmaBackend', ', '.join(histories['PharmaBackend']['fechas']), 'Rama de trabajo en 1a79813. develop pendiente de publicar.'),
    ('pharma-frontend', ', '.join(histories['pharma-frontend']['fechas']), 'develop en c72b6e1. Rama de trabajo pendiente de publicar.'),
], [4, 5.5, 7.5])
label('Historial', 'El conteo usa git log develop..HEAD y fechas reales de autor. Hay dos fechas en backend y una en frontend. Los commits adicionales del 8 de noviembre aportan evidencia de trabajo de esa jornada.')
label('Solicitudes hacia develop', 'Los textos de las solicitudes están preparados. El envío depende de publicar la rama de trabajo de cada repositorio y de contar con la rama destino remota del backend.')
label('Aula virtual', 'La copia Pacho_LP2_S13_Autonoma.pdf queda preparada para adjuntar. El comprobante de entrega está pendiente.')
label('Reproducción', 'F02-historial-PharmaBackend.txt, F02-historial-pharma-frontend.txt y F-resumen.json conservan el historial y la consulta de ramas. La guía editable describe los pasos A01 a F02.')
label('Fuentes', 'Guía de la actividad autónoma S13 de la UPeU. Documentación oficial de Angular CLI, esbuild Bundle Size Analyzer, Spring Boot Actuator, Redis TTL y Nginx proxy_pass.')
for url in ('https://angular.dev/tools/cli/build', 'https://esbuild.github.io/analyze/',
            'https://docs.spring.io/spring-boot/reference/actuator/metrics.html',
            'https://redis.io/docs/latest/commands/ttl/',
            'https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass'):
    para(url)

output = DOCS / 'Pacho_LP2_S13_Autonoma_Editable.docx'
doc.save(output)
assert hashlib.sha256(REFERENCE.read_bytes()).hexdigest() == REFERENCE_HASH
print(f'{output.name} · {figure_number} figuras')
