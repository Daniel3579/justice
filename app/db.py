import logging
import re

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHROMA_DB_PATH, CHUNK_OVERLAP, CHUNK_SIZE, DOCUMENTS_PATH
from embeddings import get_embedding_model

logging.basicConfig(level=logging.INFO)

ARTICLE_RE = re.compile(r"(?m)^[ \t]*Статья[ \t]+\d+(?:\.\d+)*\.?[^\n]*")
NOISE_RE = re.compile(
    r"(?im)^.*(КонсультантПлюс|www\.consultant\.ru|garant\.ru|Документ предоставлен|"
    r"Дата сохранения|надежная правовая поддержка|^\s*Страница\s+\d+\s+из\s+\d+).*$"
)


def clean_text(text: str) -> str:
    text = NOISE_RE.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()

# обн. метод находит конкретные статьи в документах
def split_articles(text: str) -> list[tuple[str, str]]:
    matches = list(ARTICLE_RE.finditer(text))
    if not matches:
        return [("", text)]
    parts = []
    preamble = text[:matches[0].start()].strip()
    if preamble:
        parts.append(("", preamble))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        header = " ".join(m.group(0).split())[:200]
        parts.append((header, text[m.start():end].strip()))
    return parts


def load_documents() -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    documents = []

    for pdf in sorted(DOCUMENTS_PATH.rglob("*.pdf")):
        pages = PyPDFLoader(str(pdf)).load()
        text = clean_text("\n".join(p.page_content for p in pages))
        if not text:
            logging.warning(f"Пустой текст (скан без текстового слоя?): {pdf.name}")
            continue

        title = pdf.stem
        count = 0
        for header, body in split_articles(text):
            for piece in splitter.split_text(body):
                if header and not piece.startswith(header[:30]):
                    piece = f"{header}\n{piece}"
                documents.append(Document(
                    page_content=piece,
                    metadata={"source": str(pdf), "title": title, "article": header},
                ))
                count += 1
        logging.info(f"{pdf.name}: {count} чанков")

    return documents


def build_chroma_db():
    if not DOCUMENTS_PATH.exists():
        raise FileNotFoundError(f"Нет папки {DOCUMENTS_PATH}")

    documents = load_documents()
    if not documents:
        raise RuntimeError(f"В {DOCUMENTS_PATH} нет PDF с текстом")
    logging.info(f"Всего чанков: {len(documents)}")

    Chroma.from_documents(
        documents=documents,
        embedding=get_embedding_model(),
        persist_directory=str(CHROMA_DB_PATH),
    )
    print(f"База сохранена в {CHROMA_DB_PATH}")


def load_chroma_db():
    return Chroma(
        persist_directory=str(CHROMA_DB_PATH),
        embedding_function=get_embedding_model(),
    )