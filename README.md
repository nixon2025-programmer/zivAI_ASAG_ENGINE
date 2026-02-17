# zivAI_ASAG_ENGINE
# ASAG Engine (Local RAG + Ollama)

Production-ready **Automatic Short Answer Grading (ASAG)** engine built using:

- LangChain
- Ollama (local LLM)
- FAISS vector search
- Marking-scheme-first retrieval
- Strict JSON scoring (Pydantic validated)
- Flask API (Postman testable)

This system runs fully locally and keeps **MindSpore separate** for later training experiments.

---

# Architecture Overview

## Runtime Engine (Production)

PDFs → Chunking → Embeddings (Ollama)  
        ↓  
   FAISS Indexes  
        ↓  
Dual Retrieval:
  1) Marking scheme (priority)
  2) Past exam questions (support)
        ↓  
LLM (Ollama chat model)
        ↓  
Strict JSON Grading Output
        ↓  
Flask API

---

## Research Layer (Optional)

mindspore_lab/
(separate virtual environment)


MindSpore is not required for the runtime engine.

---

# Project Structure

asag-engine/
├── data/
│ ├── raw/
│ │ ├── exams/
│ │ └── markschemes/
│ ├── processed/
│ └── indexes/
│ ├── exams_faiss/
│ └── markschemes_faiss/
│
├── src/
│ └── asag_engine/
│ ├── ingest/
│ ├── index/
│ ├── rag/
│ ├── grading/
│ └── api/
│
├── mindspore_lab/
├── requirements.txt
├── pyproject.toml
└── README.md


---

# System Requirements

- Windows + WSL2 (recommended)
- Python 3.10+
- Ollama installed on Windows
- Minimum 4GB RAM (8GB recommended)
- Internet only needed to download models

---

# Step 1 — Install Ollama (Windows)

Download from:

https://ollama.com

Verify installation:

```powershell
ollama ls
Pull required models:

ollama pull llama3:3b
ollama pull nomic-embed-text
If your RAM is limited, use:

ollama pull phi3:mini
Step 2 — Allow WSL to Access Ollama
From WSL:

WIN_HOST=$(grep -m1 nameserver /etc/resolv.conf | awk '{print $2}')
curl http://$WIN_HOST:11434/api/tags
If JSON returns, use that IP in your .env.

If blocked, allow firewall access in Windows:

New-NetFirewallRule -DisplayName "Ollama 11434" -Direction Inbound -Protocol TCP -LocalPort 11434 -Action Allow
Step 3 — Setup Python Environment
cd ~/asag-engine
/usr/bin/python3 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt
pip install -e .
Verify:

which python
It should point to:

~/asag-engine/.venv/bin/python
Step 4 — Configure .env
Create a .env file in project root:

HOST=127.0.0.1
PORT=8000

OLLAMA_BASE_URL=http://<WINDOWS_IP>:11434
OLLAMA_CHAT_MODEL=llama3:3b
OLLAMA_EMBED_MODEL=nomic-embed-text:latest

TOP_K_MARKSCHEME=3
TOP_K_EXAMS=2

DATA_DIR=data
INDEX_DIR=data/indexes
Replace <WINDOWS_IP> using:

grep -m1 nameserver /etc/resolv.conf | awk '{print $2}'
Step 5 — Add PDFs
Place files in:

data/raw/exams/
data/raw/markschemes/
Step 6 — Ingest PDFs
python -m asag_engine.ingest.ingest_cli \
  --exams_dir data/raw/exams \
  --markschemes_dir data/raw/markschemes
This generates:

data/processed/exams.jsonl
data/processed/markschemes.jsonl
Step 7 — Build Vector Indexes
rm -rf data/indexes/exams_faiss data/indexes/markschemes_faiss
python -m asag_engine.index.build_indexes
Verify:

ls data/indexes/markschemes_faiss
ls data/indexes/exams_faiss
You should see:

index.faiss
index.pkl
Step 8 — Start API
python -m asag_engine.api.app
Health check:

curl http://127.0.0.1:8000/health
Expected:

{"status":"ok"}
Postman Test
Endpoint
POST

http://127.0.0.1:8000/api/v1/grade
Body (JSON)
{
  "question_text": "Solve for x: 2x + 3 = 11",
  "student_answer": "2x = 8 so x = 4",
  "max_marks": 2
}
Example Response
{
  "score_awarded": 2,
  "max_score": 2,
  "mark_points_awarded": [
    {
      "point": "Correct rearrangement",
      "marks": 1,
      "justification": "2x = 8"
    },
    {
      "point": "Correct solution",
      "marks": 1,
      "justification": "x = 4"
    }
  ],
  "missing_points": [],
  "feedback_short": "Correct method and final answer.",
  "sources": []
}
Memory Optimization
If you see:

model requires more system memory than available
Switch to smaller model:

OLLAMA_CHAT_MODEL=phi3:mini
Or reduce retrieval:

TOP_K_MARKSCHEME=2
TOP_K_EXAMS=1
Common Issues
Issue	Solution
Connection refused	Check OLLAMA_BASE_URL
Missing index.faiss	Rebuild indexes
ModuleNotFoundError	Run pip install -e .
Not enough memory	Use smaller model
Postman cannot connect	Use WSL IP instead of localhost
Optional: MindSpore Research Folder
mindspore_lab/ is intended for:

Fine-tuning experiments

Knowledge tracing models

Rubric learning systems

Custom grading classifiers

Keep it in a separate virtual environment to avoid dependency conflicts.

Production Hardening Recommendations
Add request logging

Add timeout protection

Add input size limits

Add batch grading endpoint

Limit prompt size

Cap awarded marks to max_score

Use Gunicorn + Nginx for deployment

Add authentication if exposing publicly

Future Improvements
Structured question parser (Q3(a)(ii))

Rubric extraction from marking schemes

Multi-step reasoning grader

Batch grading API

Student knowledge tracing integration

Dockerized deployment

Summary
This ASAG Engine provides:

Fully local AI grading

Marking-scheme-first RAG

Strict JSON output

Production-ready API

Postman testable

Memory optimized

MindSpore-ready research extension