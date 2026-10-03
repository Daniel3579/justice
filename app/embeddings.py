from langchain_ollama import OllamaEmbeddings
from config import EMBEDDING_MODEL

def get_embedding_model():
    return OllamaEmbeddings(model=EMBEDDING_MODEL)