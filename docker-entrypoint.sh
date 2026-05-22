#!/bin/bash
set -e

if [ ! -d "/app/db/my_database" ]; then
    echo "========================================================================"
    echo "  FAISS database non trovato. Generazione in corso da seed data..."
    echo "========================================================================"
    python /app/scripts/seed_faiss.py
else
    echo "FAISS database esistente. Avvio diretto."
fi

exec python /app/backend.py
