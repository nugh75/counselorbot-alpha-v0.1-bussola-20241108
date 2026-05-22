# Progetto Bussola — Tutor Orientatore AI

## Panoramica
Bussola è un tutor virtuale di orientamento scolastico e professionale basato su intelligenza artificiale. È progettato per supportare studenti, NEET e giovani adulti nella scoperta del proprio percorso formativo e professionale attraverso un colloquio strutturato e personalizzato.

## Obiettivi
- Fornire orientamento personalizzato gratuito a chiunque ne abbia bisogno
- Aiutare gli utenti a identificare i propri interessi, competenze e obiettivi
- Suggerire percorsi di studio, corsi di formazione e opportunità lavorative
- Promuovere l'autoconsapevolezza e la riflessione critica sulle proprie capacità
- Ridurre la dispersione scolastica e supportare l'inclusione sociale

## Metodologia — Le 6 Fasi del Colloquio Orientativo
Il colloquio si sviluppa in sei fasi progressive:

### Fase 1: Accoglienza e Creazione di un Rapporto Empatico
Il tutor accoglie l'utente con un tono caloroso e non giudicante, lo invita a presentarsi e a condividere le sue motivazioni. L'obiettivo è creare un ambiente sicuro e di fiducia.

### Fase 2: Raccolta di Informazioni e Definizione del Profilo
Il tutor raccoglie informazioni su interessi, esperienze scolastiche/lavorative, competenze trasversali e aspirazioni. Viene tracciato un profilo preliminare dell'utente.

### Fase 3: Analisi, Sintesi e Suggerimenti Personalizzati
Sulla base delle informazioni raccolte, il tutor propone opzioni concrete: percorsi di studio, corsi professionali, certificazioni, stage o opportunità lavorative, tenendo conto del contesto territoriale.

### Fase 4: Stimolo alla Riflessione e all'Auto-consapevolezza
Il tutor incoraggia l'utente a riflettere sulle proprie scelte, a valutare i pro e i contro delle opzioni disponibili e a sviluppare un pensiero critico autonomo.

### Fase 5: Supporto Continuo e Risorse Aggiuntive
Il tutor fornisce link a risorse esterne: centri per l'impiego, sportelli di orientamento, servizi territoriali, borse di studio, informazioni su test d'ingresso e iscrizioni.

### Fase 6: Monitoraggio, Aggiornamento e Miglioramento
Il tutor rimane aggiornato sulle novità formative e lavorative e invita l'utente a tornare per eventuali aggiornamenti o nuove esigenze.

## Tecnologia
- **Backend**: Python con FastAPI
- **Frontend**: HTML, CSS, JavaScript vanilla (nessun framework)
- **LLM**: Supporto multi-provider — OpenRouter, OpenAI, Groq, Together.ai, DeepSeek
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 tramite HuggingFace
- **Vector DB**: FAISS (locale con indicizzazione semantica)
- **Librerie**: LangChain per orchestrazione LLM, PyPDF2 per PDF, python-docx per DOCX, python-pptx per PPTX

## Funzionalità Principali
- **Chat interattiva**: interfaccia disponibile in tre modalità (widget, sidebar laterale, fullscreen)
- **RAG context-aware**: il chatbot risponde attingendo a una knowledge base vettoriale costruita sui documenti caricati
- **Upload documenti**: supporto per PDF, DOCX, PPTX con estrazione automatica del testo e chunking semantico
- **FAISS admin**: endpoint per caricare, elencare e rimuovere documenti dall'indice vettoriale
- **Sistema di prompting strutturato**: il system prompt guida il comportamento del tutor seguendo le 6 fasi del colloquio

## Pubblico Target
- Studenti delle scuole superiori (14-19 anni) in fase di scelta del percorso post-diploma
- Studenti universitari che valutano un cambio di corso o un percorso specialistico
- NEET (Not in Education, Employment, or Training) tra i 15 e i 29 anni
- Giovani adulti in transizione scuola-lavoro
- Adulti che desiderano riqualificarsi o cambiare carriera

## Architettura del Sistema
Il sistema è composto da un backend FastAPI che espone API REST, un frontend statico servito direttamente dal backend, e un database vettoriale FAISS per la ricerca semantica. Le embeddings sono generate localmente tramite HuggingFace. La comunicazione con il LLM avviene tramite API HTTP standard (Chat completions). Non è richiesto un database SQL: la persistenza è affidata a file JSON (registry dei documenti) e al file system locale per gli indici vettoriali.
