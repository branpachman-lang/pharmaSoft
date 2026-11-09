"""Reúne el informe, las guías y las dos rondas de evidencia S13."""

from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

from pypdf import PdfReader

docs = Path(__file__).resolve().parents[1]
root = docs.parents[1]
report = docs / 'Pacho_LP2_S13_Autonoma.pdf'
output = docs / 'Pacho_LP2_S13_Entregables.zip'
first_round = docs / 'evidencias-s13'
manifest = json.loads((first_round / 'manifest-sha256.json').read_text(encoding='utf-8'))
for name, expected_hash in manifest.items():
    data = (first_round / name).read_bytes()
    if Path(name).suffix in {'.json', '.txt'} and sha256(data).hexdigest() != expected_hash:
        data = data.replace(b'\r\n', b'\n')
    assert sha256(data).hexdigest() == expected_hash, name
assert report.read_bytes() == (docs / 'informe-s13.pdf').read_bytes()

files = {name: docs / name for name in (
    report.name, 'Pacho_LP2_S13_Autonoma_Editable.docx', 'informe-s13.md',
    'Guia_S13_Autonoma_Paso_a_Paso.pdf', 'Guia_S13_Autonoma_Paso_a_Paso.docx',
    'Guia_S13_Autonoma_Paso_a_Paso.md', 'Checklist_capturas_S13_Autonoma.md',
)}
for folder in (first_round, docs / 'evidencias-s13-autonoma-manual'):
    files.update({item.relative_to(docs).as_posix(): item for item in sorted(folder.rglob('*'))
                  if item.is_file() and item.suffix in {'.json', '.txt', '.png', '.jpg'}})
for name in ('reproducir.md', 'medir.mjs', 'pruebas-ronda-pc.mjs'):
    files[f's13/{name}'] = docs / 's13' / name

commits = {}
for repo in ('PharmaBackend', 'pharma-frontend'):
    files[f'{repo}/README.md'] = root / repo / 'README.md'
    files[f'{repo}/solicitud-incorporacion.md'] = root / repo / 'docs/s13/solicitud-incorporacion.md'
    commits[repo] = subprocess.check_output(
        ['git', '-C', str(root / repo), 'log', '-1', '--format=%h %ad', '--date=short'],
        text=True,
    ).strip()

jwt_pattern = re.compile(r'\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{10,}')
for name, path in files.items():
    if path.suffix in {'.json', '.txt', '.md', '.mjs'}:
        assert not jwt_pattern.search(path.read_text(encoding='utf-8-sig')), name

report_pages = len(PdfReader(report).pages)
guide_pages = len(PdfReader(files['Guia_S13_Autonoma_Paso_a_Paso.pdf']).pages)
evidence = docs / 'evidencias-s13-autonoma-manual/2026-11-08-parte-f/F-resumen.json'
test_counts = json.loads(evidence.read_text(encoding='utf-8-sig'))
with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
    for name, path in files.items():
        archive.write(path, name)
    archive.writestr('ESTADO-DE-ENTREGA.txt',
        'Actividad autónoma S13 · PharmaSoft\n\n'
        f'Informe de {report_pages} páginas, guía de {guide_pages} páginas y evidencias de dos rondas.\n'
        f'Pruebas aprobadas sobre los commits de entrega: {test_counts["frontend"]["pruebas"]} de frontend y '
        f'{test_counts["backend"]["pruebas"]} de backend.\n'
        'Los seis casos de invalidación quedaron verificados. El backend quedó en UP con TTL de 10 minutos.\n\n'
        'Últimos commits locales al empaquetar:\n' + '\n'.join(f'{name} · {commit}' for name, commit in commits.items()) + '\n\n'
        'Pendientes: tres fechas reales por repositorio, solicitudes hacia develop y carga del PDF al aula virtual.\n'
        'Los textos propuestos de las solicitudes se incluyen junto a los README.\n')
with ZipFile(output) as archive:
    assert archive.testzip() is None
    print(f'{output.name} · {len(archive.namelist())} archivos · {output.stat().st_size} bytes')
