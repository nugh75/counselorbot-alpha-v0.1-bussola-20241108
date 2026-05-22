import logging
import os
import sys
from typing import List

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

import faiss_manager
from file_processor import extract_file_content, create_documents_from_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower()

PROVIDER_CONFIG = {
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "base_url": None,
    },
    "openrouter": {
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "model": os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free"),
        "base_url": "https://openrouter.ai/api/v1",
    },
    "groq": {
        "api_key": os.getenv("GROQ_API_KEY"),
        "model": os.getenv("GROQ_MODEL", "llama3-8b-8192"),
        "base_url": "https://api.groq.com/openai/v1",
    },
    "togetherai": {
        "api_key": os.getenv("TOGETHERAI_API_KEY"),
        "model": os.getenv("TOGETHERAI_MODEL", "mistralai/Mixtral-8x7B-Instruct-v0.1"),
        "base_url": "https://api.together.xyz/v1",
    },
    "deepseek": {
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "base_url": "https://api.deepseek.com",
    },
}

if LLM_PROVIDER not in PROVIDER_CONFIG:
    logger.warning(f"Provider '{LLM_PROVIDER}' sconosciuto, uso 'openai' di fallback.")
    LLM_PROVIDER = "openai"

cfg = PROVIDER_CONFIG[LLM_PROVIDER]
if not cfg["api_key"]:
    logger.error(f"Nessuna API key configurata per il provider '{LLM_PROVIDER}'.")
    sys.exit(f"ERRORE: Aggiungi {LLM_PROVIDER.upper()}_API_KEY in .env")

logger.info(f"Provider LLM: {LLM_PROVIDER} | Modello: {cfg['model']}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(BASE_DIR, "static")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_FOLDER = os.path.join(BASE_DIR, "db")
os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DB_FOLDER, exist_ok=True)

HUGGINGFACE_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CACHE_FOLDER = os.path.join(BASE_DIR, "huggingface_cache")

_embeddings = None
_faiss_index = None
_FAISS_UNAVAILABLE = object()


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=HUGGINGFACE_MODEL_NAME,
            cache_folder=CACHE_FOLDER,
        )
        logger.info(f"Embeddings caricati: {HUGGINGFACE_MODEL_NAME}")
    return _embeddings


def get_faiss_index():
    global _faiss_index
    if _faiss_index is None:
        db_path = os.path.join(DB_FOLDER, "my_database")
        try:
            _faiss_index = FAISS.load_local(
                db_path,
                get_embeddings(),
                allow_dangerous_deserialization=True,
            )
            logger.info(f"FAISS caricato da {db_path}")
        except Exception as e:
            logger.warning(f"FAISS non caricato ({e})")
            _faiss_index = _FAISS_UNAVAILABLE
    return None if _faiss_index is _FAISS_UNAVAILABLE else _faiss_index


def get_llm(temperature: float = 0.7):
    kwargs = {
        "model": cfg["model"],
        "api_key": cfg["api_key"],
        "temperature": temperature,
        "request_timeout": 60,
    }
    if cfg["base_url"]:
        kwargs["base_url"] = cfg["base_url"]
    return ChatOpenAI(**kwargs)


def _to_langchain_messages(messages: list) -> list:
    role_map = {
        "system": SystemMessage,
        "user": HumanMessage,
        "assistant": AIMessage,
    }
    result = []
    for m in messages:
        cls = role_map.get(m["role"])
        if cls:
            result.append(cls(content=m["content"]))
    return result


def retrieve_context(query: str) -> List[dict]:
    index = get_faiss_index()
    if not index:
        logger.warning("FAISS non disponibile.")
        return []
    if not query.strip():
        return []
    try:
        docs = index.similarity_search(query, k=5)
        logger.info(f"{len(docs)} documenti trovati per: '{query}'")
        return [
            {
                "content": doc.page_content,
                "source": {
                    "filename": doc.metadata.get("filename", "sconosciuto"),
                    "page_number": doc.metadata.get("page_number", "n/a"),
                },
            }
            for doc in docs
        ]
    except Exception as e:
        logger.error(f"Errore retrieve_context: {e}")
        return []


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_FOLDER), name="static")


@app.get("/", response_class=FileResponse)
async def serve_index():
    path = os.path.join(STATIC_FOLDER, "index.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="index.html non trovato")
    return FileResponse(path)


@app.get("/embed", response_class=FileResponse)
async def serve_embed():
    path = os.path.join(STATIC_FOLDER, "embed.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="embed.html non trovato")
    return FileResponse(path)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


class ChatRequest(BaseModel):
    messages: List[dict]
    temperature: float = 0.7


@app.post("/v1/chat/completions")
async def chat_completion(request: ChatRequest):
    try:
        user_message = request.messages[-1]["content"]
        logger.info(f"Messaggio utente: {user_message}")

        context = retrieve_context(user_message)

        augmented = list(request.messages)
        if context:
            context_text = "\n".join(
                f"– {c['content']} (Fonte: {c['source']['filename']}, Pagina: {c['source']['page_number']})"
                for c in context
            )
            for msg in augmented:
                if msg["role"] == "system":
                    msg["content"] = f"{msg['content']}\n\nContesto:\n{context_text}"
                    break
            else:
                augmented.insert(0, {"role": "system", "content": f"Contesto:\n{context_text}"})

        lc_messages = _to_langchain_messages(augmented)
        llm = get_llm(request.temperature)
        response = llm.invoke(lc_messages)
        logger.info(f"Risposta LLM: {response.content[:100]}...")

        return {"llm_response": response.content, "context_chunks": context or []}
    except Exception as e:
        logger.error(f"Errore chat_completion: {e}")
        err = str(e)
        if "insufficient_quota" in err:
            detail = "Credito insufficiente per il provider attuale."
        elif "rate_limit" in err.lower() or "429" in err:
            detail = "Limite di richieste superato. Attendi e riprova."
        else:
            detail = err
        raise HTTPException(status_code=500, detail=detail)


@app.post("/upload-and-process")
async def upload_and_process(file: UploadFile = File(...)):
    try:
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(path, "wb") as f:
            f.write(file.file.read())
        text = extract_file_content(path)
        return {"message": "File processato", "extracted_text": text}
    except Exception as e:
        logger.error(f"upload_and_process error: {e}")
        raise HTTPException(status_code=500, detail="Errore elaborazione file.")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(path, "wb") as f:
            f.write(file.file.read())
        content = extract_file_content(path)
        lines = content.split("\n")
        return {
            "message": "File caricato",
            "filename": file.filename,
            "content": [l for l in lines[:5] if l.strip()],
        }
    except Exception as e:
        logger.error(f"upload error: {e}")
        raise HTTPException(status_code=500, detail="Errore upload.")


@app.post("/faiss/upload")
async def upload_file_to_faiss(file: UploadFile = File(...)):
    try:
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(path, "wb") as f:
            f.write(file.file.read())
        documents = create_documents_from_file(path)
        result = faiss_manager.add_documents(
            [{"content": d.page_content, "metadata": d.metadata} for d in documents]
        )
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        global _faiss_index
        _faiss_index = None
        return {"message": "File aggiunto al database FAISS", "filename": file.filename}
    except Exception as e:
        logger.error(f"faiss/upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/faiss/list")
async def list_faiss_documents():
    try:
        return faiss_manager.list_documents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/faiss/remove-file/{filename}")
async def remove_file_from_faiss(filename: str):
    try:
        result = faiss_manager.remove_documents_by_filename(filename)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        global _faiss_index
        _faiss_index = None
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/faiss")
async def debug_faiss():
    index = get_faiss_index()
    if not index:
        return {"message": "FAISS non caricato."}
    try:
        docs = index.similarity_search("debug", k=5)
        return {"documents": [d.page_content[:200] for d in docs]}
    except Exception as e:
        logger.error(f"debug_faiss: {e}")
        return {"message": "Errore debug FAISS."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
