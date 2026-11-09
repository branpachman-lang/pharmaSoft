"""Guía manual S13 con estilos conservados del DOCX práctico de la sesión."""
from pathlib import Path
import re, json, hashlib, shutil, copy
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[3]
REF=ROOT/'pharma-frontend/docs/Pacho_LP2_S13_Practica_Editable.docx'
SOURCE=Path(__file__).with_name('guia-manual-s13.md')
DEST=ROOT/'PharmaBackend/docs/Guia_S13_Autonoma_Paso_a_Paso.docx'
expected='b59d1341619b62ddf8527acf920facef21716b66dd74285b2b17c57d623e92e8'
assert hashlib.sha256(REF.read_bytes()).hexdigest()==expected, 'Cambió la referencia de diseño.'
original=Document(REF)
doc=Document(REF)
body=doc._element.body
for element in list(body):
    if element.tag!=qn('w:sectPr'): body.remove(element)
# No transportar las capturas antiguas ni sus datos a una guía nueva.
for key, rel in list(doc.part.rels.items()):
    if rel.reltype.endswith('/image'): del doc.part.rels[key]
doc.core_properties.title='Guía de pruebas y capturas de la actividad autónoma de PharmaSoft'
doc.core_properties.subject='Procedimientos manuales de las partes A a F de S13'
doc.core_properties.author='Brandon Erly Pacho Mamani'
doc.core_properties.comments=''
settings=doc.settings.element
update=settings.find(qn('w:updateFields'))
if update is None: update=OxmlElement('w:updateFields'); settings.append(update)
update.set(qn('w:val'),'true')
footer=doc.sections[0].footer.paragraphs[0]
footer.clear();footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('Sesión 13 autónoma  |  Página ').font.size=Pt(8)
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)

def rich(p,text):
    for part in re.split(r'(\*\*.*?\*\*|`[^`]+`)',text):
        if part.startswith('**') and part.endswith('**'): p.add_run(part[2:-2]).bold=True
        elif part.startswith('`') and part.endswith('`'):
            r=p.add_run(part[1:-1]);r.font.name='Consolas';r.font.size=Pt(8.5)
        else:p.add_run(part)
    return p

def paragraph(text, style=None):
    p=doc.add_paragraph(style=style)
    rich(p,text)
    p.paragraph_format.widow_control=True
    if re.match(r'^\d+\. ',text):
        p.paragraph_format.left_indent=Cm(.55)
        p.paragraph_format.first_line_indent=Cm(-.55)
    return p

def make_table(lines):
    rows=[[x.strip() for x in line.strip().strip('|').split('|')] for line in lines if not re.match(r'^\|\s*-',line)]
    t=doc.add_table(rows=0,cols=len(rows[0]));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    widths=[2.3,2.7,5,7] if len(rows[0])==4 else [17/len(rows[0])]*len(rows[0])
    for n,row in enumerate(rows):
        cells=t.add_row().cells
        trpr=t.rows[-1]._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
        if n==0:trpr.append(OxmlElement('w:tblHeader'))
        for i,(cell,value) in enumerate(zip(cells,row)):
            cell.width=Cm(widths[i]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            rich(cell.paragraphs[0],value)
            tcpr=cell._tc.get_or_add_tcPr()
            b=OxmlElement('w:tcBorders')
            for side in ['top','left','bottom','right']:
                edge=OxmlElement('w:'+side)
                for key,val in [('val','single'),('sz','4'),('color','D9D9D9')]:edge.set(qn('w:'+key),val)
                b.append(edge)
            tcpr.append(b)
            mar=OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                element=OxmlElement('w:'+side);element.set(qn('w:w'),'95');element.set(qn('w:type'),'dxa');mar.append(element)
            tcpr.append(mar)
            shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E2EAF2' if n==0 else ('F5F7FA' if n%2==0 else 'FFFFFF'));tcpr.append(shade)
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2)
                if i==0:p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:r.font.size=Pt(9);r.bold=(n==0)
    doc.add_paragraph()

source=SOURCE.read_text(encoding='utf-8')
lines=source.splitlines();i=0;code=False
cases=[];captures=[];current='Preparación';first_h1=True
active_case=False
def completion_fields():
    paragraph('**Resultado observado:** Pendiente de tu ejecución. Registrar aquí cifras, IDs y lo que realmente ocurrió.')
    paragraph('**Estado:** Pendiente. Cambiar a Conforme, No conforme o Evidencia incompleta al revisar las capturas.')
    paragraph('**Evidencias adjuntas:** Anotar los nombres de los archivos que respaldan esta ficha.')
while i<len(lines):
    line=lines[i].rstrip();i+=1
    if line.startswith('```'):
        code=not code;continue
    if code:
        p=doc.add_paragraph();p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1
        r=p.add_run(line or ' ');r.font.name='Consolas';r.font.size=Pt(8)
        continue
    if not line:continue
    if line.startswith('# '):paragraph(line[2:],'Title');continue
    if line=='Actividad autónoma de la sesión 13':paragraph(line,'Subtitle');continue
    if line.startswith('## '):
        title=line[3:]
        if active_case:
            completion_fields();active_case=False
        if re.match(r'^[A-F]\d\d ',title):
            cases.append(title);current=title
            active_case=True
            doc.add_page_break()
        elif title.startswith(('Preparación común','Matriz que','Anexo ','Referencias')):doc.add_page_break()
        paragraph(title,'Heading 1');continue
    if line.startswith('|'):
        tab=[line]
        while i<len(lines) and lines[i].startswith('|'):tab.append(lines[i]);i+=1
        make_table(tab);continue
    names=re.findall(r'`(AA-[A-Za-z0-9-]+\.png)`',line)
    for name in names:
        if name not in [x['archivo'] for x in captures]: captures.append({'archivo':name,'ficha':current})
    if line.startswith('- '):paragraph('• '+line[2:])
    else:paragraph(line)

if active_case:completion_fields()

# Conservación de geometría y estilos de la referencia.
assert doc.sections[0]._sectPr.xml==original.sections[0]._sectPr.xml
assert doc.styles.element.xml==original.styles.element.xml
doc.save(DEST)
for project in ['PharmaBackend','pharma-frontend']:
    folder=ROOT/project/'docs'
    if folder/'Guia_S13_Autonoma_Paso_a_Paso.docx'!=DEST:
        shutil.copy2(DEST,folder/'Guia_S13_Autonoma_Paso_a_Paso.docx')
    (folder/'Guia_S13_Autonoma_Paso_a_Paso.md').write_text(source,encoding='utf-8')
    checklist=['# Lista de capturas de la actividad autónoma S13','',
        'Marca cada archivo cuando hayas comprobado su contenido. Las capturas compartidas se reutilizan sin repetir la venta o la medición. Los nombres de D02 de 401, 400 y 409 son complementarios; F01 también es validación complementaria.', '']
    last=None
    for row in captures:
        if last!=row['ficha']:checklist+=['','## '+row['ficha'],''];last=row['ficha']
        checklist.append('- [ ] '+row['archivo'])
    checklist+=['','En A03 conserva además las cinco repeticiones de cada variante. Añade sufijos de corrida a sus capturas. La lista marca archivos propuestos, no pruebas ya aprobadas.','']
    (folder/'Checklist_capturas_S13_Autonoma.md').write_text('\n'.join(checklist),encoding='utf-8')
(ROOT/'tmp/guia-autonoma-s13/inventario.json').write_text(json.dumps({'casos':cases,'capturas':captures},ensure_ascii=False,indent=2),encoding='utf-8')
assert hashlib.sha256(REF.read_bytes()).hexdigest()==expected
print('Fichas:',len(cases),'Capturas propuestas:',len(captures))
print(DEST)
