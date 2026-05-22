import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.text_splitter import RecursiveCharacterTextSplitter

import faiss_manager
from file_processor import create_documents_from_file

SEED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "seed-data")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "upload-files")


def process_markdown(filepath: str) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(content)
    return [
        {"content": chunk, "metadata": {"filename": os.path.basename(filepath), "page_number": i + 1}}
        for i, chunk in enumerate(chunks) if chunk.strip()
    ]


def main():
    all_docs = []

    if os.path.isdir(SEED_DIR):
        for fname in sorted(os.listdir(SEED_DIR)):
            if fname.endswith(".md"):
                fpath = os.path.join(SEED_DIR, fname)
                docs = process_markdown(fpath)
                all_docs.extend(docs)
                print(f"  ✓ {fname} → {len(docs)} chunk")

    if os.path.isdir(UPLOAD_DIR):
        for fname in sorted(os.listdir(UPLOAD_DIR)):
            ext = os.path.splitext(fname)[1].lower()
            if ext in (".pdf", ".docx", ".pptx"):
                fpath = os.path.join(UPLOAD_DIR, fname)
                docs = create_documents_from_file(fpath)
                all_docs.extend(
                    {"content": d.page_content, "metadata": d.metadata}
                    for d in docs
                )
                print(f"  ✓ {fname} → {len(docs)} chunk")

    if not all_docs:
        print("Nessun seed data trovato. Skipping.")
        return

    result = faiss_manager.add_documents(all_docs)
    if "error" in result:
        print(f"ERRORE: {result['error']}")
        sys.exit(1)

    print(f"\nFAISS popolato con {len(all_docs)} chunk totali.")


if __name__ == "__main__":
    main()
