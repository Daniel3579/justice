from langchain_ollama import OllamaEmbeddings
from config import EMBEDDING_MODEL, OLLAMA_URL

def get_embedding_model():
    return OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_URL)