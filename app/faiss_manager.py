import json
import os
import shutil
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document

HUGGINGFACE_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CACHE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "huggingface_cache")

_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=HUGGINGFACE_MODEL_NAME,
            cache_folder=CACHE_FOLDER,
        )
    return _embeddings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = os.path.join(BASE_DIR, "db")
db_path = os.path.join(DB_FOLDER, "my_database")
registry_path = os.path.join(DB_FOLDER, "registry.json")

def _ensure_db_dir():
    os.makedirs(DB_FOLDER, exist_ok=True)

def _load_registry() -> list:
    if not os.path.exists(registry_path):
        return []
    with open(registry_path, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_registry(entries: list):
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

def _rebuild_faiss(entries: list):
    _ensure_db_dir()
    if not entries:
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
        return
    docs = [
        Document(page_content=e["content"], metadata=e["metadata"])
        for e in entries
    ]
    index = FAISS.from_documents(docs, get_embeddings())
    index.save_local(db_path)

def load_faiss():
    if not os.path.exists(db_path) or not os.path.isdir(db_path):
        raise FileNotFoundError("Il database FAISS non esiste.")
    return FAISS.load_local(db_path, get_embeddings(), allow_dangerous_deserialization=True)

def add_documents(documents: list) -> dict:
    try:
        _ensure_db_dir()
        registry = _load_registry()
        new_entries = [
            {"content": doc["content"], "metadata": doc["metadata"]}
            for doc in documents
        ]
        registry.extend(new_entries)
        _rebuild_faiss(registry)
        _save_registry(registry)
        return {"message": "Documenti aggiunti con successo."}
    except Exception as e:
        return {"error": str(e)}

def list_documents(limit: int = 50) -> list:
    entries = _load_registry()
    return [
        {
            "content_preview": e["content"][:200],
            "filename": e["metadata"].get("filename", "sconosciuto"),
            "page_number": e["metadata"].get("page_number", "n/a"),
        }
        for e in entries[:limit]
    ]

def remove_documents_by_filename(filename: str) -> dict:
    try:
        registry = _load_registry()
        filtered = [e for e in registry if e["metadata"].get("filename") != filename]
        if len(filtered) == len(registry):
            return {"message": f"Nessun documento trovato per '{filename}'."}
        _rebuild_faiss(filtered)
        _save_registry(filtered)
        return {"message": f"Documenti associati a '{filename}' rimossi con successo."}
    except Exception as e:
        return {"error": str(e)}
