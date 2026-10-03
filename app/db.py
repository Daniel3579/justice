import os
import logging
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from embeddings import get_embedding_model
from config import DOCUMENTS_PATH, CHROMA_DB_PATH

logging.basicConfig(level=logging.INFO)

def build_chroma_db():
    """Собирает векторную базу из PDF в data/documents."""
    if not os.path.exists(DOCUMENTS_PATH):
        raise FileNotFoundError(f"Нет папки {DOCUMENTS_PATH} — положи туда PDF")

    loader = DirectoryLoader(
        DOCUMENTS_PATH,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True,
    )
    documents = loader.load()
    logging.info(f"Загружено {len(documents)} страниц")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, # потом снижу
        chunk_overlap=100,
        add_start_index=True,
    )
    chunks = splitter.split_documents(documents)
    logging.info(f"Нарезано {len(chunks)} чанков")

    Chroma.from_documents(
        documents=chunks,
        embedding=get_embedding_model(),
        persist_directory=CHROMA_DB_PATH,
    )
    print(f"База сохранена в {CHROMA_DB_PATH}")


def load_chroma_db():
    return Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=get_embedding_model(),
    )