from pathlib import Path
import json, xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[3]
docs=root/'PharmaBackend/docs'
files=[root/'PharmaBackend/README.md',root/'pharma-frontend/README.md',docs/'s13/reproducir.md',docs/'s13/solicitud-incorporacion.md',root/'pharma-frontend/docs/s13/solicitud-incorporacion.md',docs/'s13/generar_informe.py']
for file in files:
    text=file.read_text(encoding='utf-8').replace('41 pruebas','42 pruebas').replace('51 pruebas','53 pruebas')
    text=text.replace('La baja lógica aparece como inactiva; difiere de «ya no aparece» del enunciado C-05',
                      'Corregido: lista habitual solo de activas; Mostrar inactivas conserva la consulta administrativa')
    text=text.replace('| Baja de categoría | Cumple parcialmente |', '| Baja de categoría | Cumple |')
    text=text.replace('C-05 documenta la diferencia entre la baja lógica vigente y la ausencia literal solicitada; no se cambia el contrato de bajas para esconder el resultado.',
        'C-05 incorpora el filtro paginado soloActivas: la categoría desaparece de la vista habitual y se puede consultar con Mostrar inactivas. Se preserva la baja lógica y la consulta API por defecto.')
    text=text.replace('C-05 se registra honestamente: por la baja lógica existente, el dato pasa a inactivo pero permanece en la lista administrativa. La invalidación sí funciona; no es un defecto de `@CacheEvict`.',
        'El primer ensayo C-05 mostró una baja lógica todavía visible. La corrección añade soloActivas al filtro y a la clave de caché; el listado habitual consulta activas en el servidor y Mostrar inactivas conserva la revisión administrativa. Repetir con c05-api y c05-spa. La API sin el filtro sigue devolviendo el historial para mantener compatibilidad.')
    file.write_text(text,encoding='utf-8')
suites=[ET.parse(f).getroot() for f in (root/'PharmaBackend/target/surefire-reports').glob('TEST-*.xml')]
result={key:sum(int(s.get(key,'0')) for s in suites) for key in ['tests','failures','errors','skipped']}
result['excluded']='PharmaBackendApplicationTests (contexto con dependencias externas)'
(docs/'evidencias-s13/F-pruebas-backend.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(result)
