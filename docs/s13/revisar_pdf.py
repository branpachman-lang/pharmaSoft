from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
from pypdf import PdfReader
root=Path(__file__).resolve().parents[3]
pages=sorted((root/'tmp/pdfs').glob('s13-*.png'))[:len(PdfReader(root/'PharmaBackend/docs/informe-s13.pdf').pages)]
cols=4; w=310; h=460
sheet=Image.new('RGB',(cols*w,((len(pages)+cols-1)//cols)*h),'#dbe3ec')
draw=ImageDraw.Draw(sheet)
for i,p in enumerate(pages):
    im=Image.open(p); im.thumbnail((290,425))
    x=(i%cols)*w+10; y=(i//cols)*h+25
    sheet.paste(im,(x,y)); draw.text((x,y-18),p.name,fill='black')
sheet.save(root/'tmp/pdfs/revision.png')
