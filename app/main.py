from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
import os
import re
import tempfile
from pydantic import BaseModel

from docx import Document

from generator import generate_isk

app = FastAPI(title="Генератор исков")

class AskRequest(BaseModel):
    text: str


def clean_text(text: str) -> str:
    # очистка текстового мусора
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    # переводы строк
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def text_to_docx(text: str, path: str):
    # текст в .docx с форматированием
    from docx.shared import Pt
    from docx.oxml.ns import qn

    doc = Document()

    # шрифт
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(14)
    # фикс для кириллицы 
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")

    #  параграфы
    for line in text.split("\n"):
        line = line.rstrip()
        if not line:
            doc.add_paragraph("")
        else:
            p = doc.add_paragraph(line)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            # принудительно шрифт каждому run
            for run in p.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(14)
                run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")

    doc.save(path)


@app.post("/generate")
async def generate(req: AskRequest):
    # возвращает JSON для отладки
    user_text = req.text.strip()
    if not user_text:
        return JSONResponse({"error": "Поле 'text' обязательно"}, status_code=400)

    try:
        result = generate_isk(user_text)
        return {
            "facts": result["facts"],
            "isk": result["isk"],
            "sources": {
                "local": result["local_norms"][:2000],
                "web": result["web_norms"][:2000],
            }
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/generate/docx")
async def generate_docx(req: AskRequest):
    # возвращает иск как .docx файл
    user_text = req.text.strip()
    if not user_text:
        return JSONResponse({"error": "Поле 'text' обязательно"}, status_code=400)

    try:
        result = generate_isk(user_text)
        isk_text = clean_text(result["isk"])

        # временный файл
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".docx", prefix="isk_"
        )
        tmp.close()
        text_to_docx(isk_text, tmp.name)

        return FileResponse(
            tmp.name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="iskovoe_zayavlenie.docx",
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/generate/txt")
async def generate_txt(req: AskRequest):
    """Возвращает иск как .txt — если docx не нужен."""
    user_text = req.text.strip()
    if not user_text:
        return JSONResponse({"error": "Поле 'text' обязательно"}, status_code=400)

    try:
        result = generate_isk(user_text)
        isk_text = clean_text(result["isk"])

        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".txt", prefix="isk_",
            mode="w", encoding="utf-8"
        )
        tmp.write(isk_text)
        tmp.close()

        return FileResponse(
            tmp.name,
            media_type="text/plain; charset=utf-8",
            filename="iskovoe_zayavlenie.txt",
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)