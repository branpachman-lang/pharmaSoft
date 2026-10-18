"""Genera el informe editable de la actividad autónoma S10."""
from pathlib import Path
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "Pacho_LP2_S10_Autonoma_Editable.docx"

doc = Document()
section = doc.sections[0]
section.page_width = Inches(8.5)
section.page_height = Inches(11)
section.top_margin = Inches(.72)
section.bottom_margin = Inches(.65)
section.left_margin = Inches(.82)
section.right_margin = Inches(.82)

styles = doc.styles
styles["Normal"].font.name = "Aptos"
styles["Normal"].font.size = Pt(10.5)
styles["Normal"].font.color.rgb = RGBColor(24, 33, 43)
styles["Normal"].paragraph_format.space_after = Pt(6)
for name, size, before, after in [("Title", 18, 0, 10), ("Heading 1", 12.5, 14, 6), ("Heading 2", 11, 10, 4)]:
    style = styles[name]
    style.font.name = "Aptos Display" if name == "Title" else "Aptos"
    style.font.size = Pt(size)
    style.font.bold = True
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.space_before = Pt(before)
    style.paragraph_format.space_after = Pt(after)
    if name == "Title":
        ppr = style._element.get_or_add_pPr()
        for border in ppr.findall(qn("w:pBdr")):
            ppr.remove(border)

def set_cell_shading(cell, fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tcpr.append(shd)

def set_borders(table):
    tblpr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = OxmlElement(f"w:{edge}")
        tag.set(qn("w:val"), "single")
        tag.set(qn("w:sz"), "4")
        tag.set(qn("w:color"), "D9D9D9")
        borders.append(tag)
    tblpr.append(borders)

def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    t.style = "Table Grid"
    for j, title in enumerate(headers):
        c = t.rows[0].cells[j]
        if widths: c.width = Inches(widths[j])
        c.text = title
        set_cell_shading(c, "16345D")
        for run in c.paragraphs[0].runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(9)
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        cells = t.add_row().cells
        for j, value in enumerate(row):
            if widths: cells[j].width = Inches(widths[j])
            cells[j].text = str(value)
            cells[j].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for p in cells[j].paragraphs:
                p.paragraph_format.space_after = Pt(1)
                for run in p.runs: run.font.size = Pt(9)
            if i % 2: set_cell_shading(cells[j], "F3F6FA")
    set_borders(t)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t

doc.add_paragraph("Informe de seguridad y gestión de usuarios", "Title")
p = doc.add_paragraph()
p.add_run("Actividad autónoma · Sesión 10 · Lenguaje de Programación II\n").bold = True
p.add_run("Estudiante: Pacho    Proyecto: PharmaBackend    Rama: feature/seguridad-pruebas-pacho")

doc.add_heading("Alcance y método", 1)
doc.add_paragraph(
    "Este informe reúne los resultados de la matriz de 28 casos sobre autenticación, JWT, permisos, usuarios y CORS, "
    "junto con la verificación del cambio de contraseña, la asignación de roles y la desactivación de cuentas. "
    "La colección Postman contiene las solicitudes; la matriz y sus capturas constituyen la evidencia. "
    "Completar los campos entre corchetes únicamente después de ejecutar las peticiones."
)

doc.add_heading("C1 Resumen de resultados", 1)
table(["Grupo", "Casos", "Pasan", "Fallan"], [
    ("Autenticación", "5", "[ ]", "[ ]"), ("Token", "6", "[ ]", "[ ]"),
    ("Permisos", "5", "[ ]", "[ ]"), ("Usuarios", "3", "[ ]", "[ ]"),
    ("CORS", "1", "[ ]", "[ ]"), ("Contraseña, roles y estado", "8", "[ ]", "[ ]"),
    ("TOTAL", "28", "[ ]", "[ ]")
], [3.65, .9, 1.1, 1.1])
doc.add_paragraph("Resultado general: [escribir el número de casos ejecutados, los que pasan y los que fallan].")
doc.add_paragraph("Fecha y entorno de ejecución: [fecha, versión de backend, base Oracle y URL local].")

doc.add_heading("C2 Hallazgos y correcciones", 1)
doc.add_paragraph(
    "Crea una ficha por cada caso que falle. Si todos pasan, indica expresamente que no se detectaron fallas "
    "en los casos ejecutados y conserva una sola ficha marcada como no aplicable."
)
table(["Campo", "Completar con el resultado observado"], [
    ("Caso y descripción", "[ID] — [qué ocurrió frente a lo esperado]"),
    ("Severidad", "[Alta, media o baja y fundamento]"),
    ("Evidencia", "[Nombre de la captura en docs/evidencias_s10_autonoma/]"),
    ("Causa probable", "[Clase y método que podrían producir el fallo]"),
    ("Corrección propuesta", "[Cambio concreto y cómo se comprobaría]")
], [1.5, 5.25])
doc.add_paragraph(
    "Para añadir una captura a este informe, inserta solo la más representativa de cada hallazgo debajo de su ficha, "
    "con el ID y un pie breve. Las evidencias de todos los casos se enlazan en docs/matriz-seguridad-s10.md."
)

doc.add_page_break()
doc.add_heading("C3 Análisis de seguridad", 1)
doc.add_heading("1 Mensaje uniforme en el login", 2)
doc.add_paragraph(
    "El login devuelve «Usuario o contraseña incorrectos» tanto para una cuenta inexistente como para una "
    "contraseña errónea o una cuenta deshabilitada. GlobalExceptionHandler.handleAuthentication convierte los "
    "fallos de autenticación en el mismo 401. Si el mensaje distinguiera esos casos, una persona que prueba nombres "
    "de usuario podría descubrir cuáles cuentas existen y concentrar sus intentos sobre ellas."
)
doc.add_heading("2 Validez del token tras cambiar la contraseña", 2)
doc.add_paragraph(
    "El JWT anterior sigue firmado y no ha vencido; la API no mantiene una sesión que pueda cerrar al cambiar la "
    "contraseña. JwtAuthenticationFilter verifica firma y expiración y vuelve a cargar el usuario, su estado y sus "
    "permisos, pero no compara el token con el momento del cambio de contraseña. Una solución sería añadir a Usuario "
    "una versión de token que se incremente al cambiar la clave y guardar esa versión como claim. El filtro rechazaría "
    "los tokens cuya versión ya no coincida."
)
doc.add_heading("3 Exposición del secreto JWT", 2)
doc.add_paragraph(
    "Quien obtenga el secreto de firma puede crear tokens que la API considere auténticos, por ejemplo con el "
    "username de un administrador real. La respuesta inmediata es retirar el secreto del repositorio y de sus "
    "versiones publicadas, generar otro valor fuerte, actualizar el servidor y reiniciarlo para invalidar los tokens "
    "anteriores. También revisaría registros de acceso y movería el secreto a una variable de entorno o gestor de secretos."
)
doc.add_heading("4 Autorización de reportes", 2)
doc.add_paragraph(
    "@PreAuthorize en ReporteController expresa el permiso junto al método protegido y permite reglas precisas "
    "para cada operación. Su desventaja es que la política queda distribuida: al añadir un método es fácil olvidar "
    "la anotación y hay que revisar controladores y configuración para entender el conjunto. Una regla por URL en "
    "SecurityConfig reúne la política en un lugar, aunque puede resultar menos precisa si varias operaciones "
    "comparten ruta y necesitan permisos distintos."
)

footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run("PharmaSoft · LP II · S10 · Pacho").font.size = Pt(8)
doc.save(OUTPUT)
print(OUTPUT)
