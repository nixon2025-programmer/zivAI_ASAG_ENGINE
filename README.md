# ASAG Engine  
AI-Powered Adaptive Student Assessment & Generation System

An intelligent academic backend powering:

- Student Tutor Agent  
- Resource Intelligence (MindOCR + FAISS + PostgreSQL)  
- Classroom Copilot (Teacher Workflow)  
- Analytics & Learning Plans  
- AI-Assisted Grading  

---

## Overview

ASAG Engine is a modular AI academic backend built with:

- Flask API  
- PostgreSQL  
- FAISS (Vector Search)  
- Sentence Transformers  
- MindOCR (for scanned PDFs & images)  
- Ollama (LLM generation)  

It enables:

- Uploading and indexing school materials  
- Retrieving relevant snippets with citations  
- AI-powered tutoring  
- AI-generated assessments  
- Learning plan generation  
- Classroom content drafting and editing  

---

## Project Structure

```

asag-engine/
│
├── src/
│   └── asag_engine/
│       ├── api/
│       │   ├── app.py
│       │   ├── resource_routes.py
│       │   ├── tutor_routes.py
│       │   ├── copilot_routes.py
│       │   └── learning_plan_routes.py
│       │
│       ├── resource_intelligence/
│       │   ├── service.py
│       │   ├── chunking.py
│       │   ├── embeddings.py
│       │   ├── faiss_index.py
│       │   ├── models.py
│       │   └── extractors/
│       │       ├── pdf_extractor.py
│       │       ├── docx_extractor.py
│       │       ├── image_extractor.py
│       │       └── mindocr_runner.py
│       │
│       ├── tutor_agent/
│       ├── classroom_copilot/
│       ├── learning_plans/
│       ├── analytics/
│       └── config.py
│
├── data/
│   ├── indexes/resources_faiss/
│   └── raw/
│
├── requirements.txt
└── README.md

```

---

## Core Modules

### 1. Resource Intelligence

Extracts text from:

- PDF (text via PyMuPDF)  
- Scanned PDFs / Images (via MindOCR)  
- DOCX (python-docx)  

Pipeline:

1. Upload  
2. Extract  
3. Chunk  
4. Embed (Sentence Transformers)  
5. Index (FAISS)  
6. Store metadata (PostgreSQL)  

Search Flow:

1. Query  
2. FAISS similarity search  
3. Retrieve relevant chunks  
4. Return snippet with citation (including page numbers)  

This enables grounded responses and traceable academic references.

---

### 2. Student Tutor Agent

Flow:

Student Question  
→ Query FAISS  
→ Retrieve Relevant Snippets  
→ Send Snippet + Question to Ollama  
→ Generate Explanation with Citation  

Benefits:

- Grounded responses  
- Reduced hallucination  
- Step-by-step explanations  
- Context-aware tutoring  

---

### 3. Classroom Copilot

Designed for teachers.

Capabilities:

- Generate assessments  
- Edit existing drafts  
- Use uploaded school materials as context  
- Save and refine drafts  

Endpoints:

- `POST /api/v1/copilot/generate`
- `POST /api/v1/copilot/edit`

---

### 4. Learning Plans

- Weak topic detection  
- Mastery tracking  
- AI-driven practice generation  
- Student-specific adaptive plans  

---

## API Endpoints

### System

- `GET /health`  
- `GET /static/<path:filename>`

### Grading

- `POST /api/v1/grade`

### Analytics

- `GET /api/v1/analytics/student/<student_id>`

### Learning Plans

- `POST /api/v1/learning-plans/student/<student_id>`

### Tutor Agent

- `POST /api/v1/tutor/student/<student_id>`

### Resource Intelligence

- `POST /api/v1/resources/upload`
- `POST /api/v1/resources/search`

### Classroom Copilot

- `POST /api/v1/copilot/generate`
- `POST /api/v1/copilot/edit`

---

## How to Run on a New PC

### 1. Install Python (3.10+)

Verify:

```

python --version

```

---

### 2. Clone the Repository

```

git clone [https://github.com/yourusername/asag-engine.git](https://github.com/yourusername/asag-engine.git)
cd asag-engine

```

---

### 3. Create Virtual Environment

Linux / Mac:

```

python -m venv .venv
source .venv/bin/activate

```

Windows:

```

python -m venv .venv
.venv\Scripts\activate

```

---

### 4. Install Requirements

```

pip install -r requirements.txt

```

---

### 5. Install and Run Ollama

Install Ollama:

https://ollama.ai

Start server:

```

ollama serve

```

Pull model:

```

ollama pull llama3.2:1b

```

---

### 6. Install MindOCR

```

git clone [https://github.com/mindspore-lab/mindocr.git](https://github.com/mindspore-lab/mindocr.git)
cd mindocr
pip install -e .

```

Set environment variable:

Linux / Mac:

```

export MINDOCR_HOME=~/mindocr

```

Windows:

```

setx MINDOCR_HOME C:\path\to\mindocr

```

---

### 7. Setup PostgreSQL

Create database:

```

CREATE DATABASE asag_db;

```

Set environment variable:

Linux / Mac:

```

export DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/asag_db

```

Windows:

```

setx DATABASE_URL postgresql+psycopg2://postgres:password@localhost:5432/asag_db

```

---

### 8. Run Application

```

python -m asag_engine.api.app

```

Server runs at:

```

[http://127.0.0.1:8000](http://127.0.0.1:8000)

```

---

## Example CURL Requests

### Upload Resource

```

curl -X POST [http://127.0.0.1:8000/api/v1/resources/upload](http://127.0.0.1:8000/api/v1/resources/upload) 
-F "file=@data/raw/pdfs/test.pdf"

```

---

### Search Resource

```

curl -X POST [http://127.0.0.1:8000/api/v1/resources/search](http://127.0.0.1:8000/api/v1/resources/search) 
-H "Content-Type: application/json" 
-d '{"query":"Quadratic formula","top_k":5}'

```

---

### Tutor Question

```

curl -X POST [http://127.0.0.1:8000/api/v1/tutor/student/S002](http://127.0.0.1:8000/api/v1/tutor/student/S002) 
-H "Content-Type: application/json" 
-d '{"question":"Explain how to solve quadratic equations"}'

```

---

### Generate Assessment (Copilot)

```

curl -X POST [http://127.0.0.1:8000/api/v1/copilot/generate](http://127.0.0.1:8000/api/v1/copilot/generate) 
-H "Content-Type: application/json" 
-d '{
"task_type": "assessment",
"topic": "Quadratic Equations",
"grade_level": "Form 3",
"instructions": "Include word problems and mark allocation."
}'

```

---

### Edit Generated Content

```

curl -X POST [http://127.0.0.1:8000/api/v1/copilot/edit](http://127.0.0.1:8000/api/v1/copilot/edit) 
-H "Content-Type: application/json" 
-d '{
"draft_id": "draft_001",
"instructions": "Make it harder and add marking scheme."
}'

```

---

## Summary

ASAG Engine is a production-ready AI academic backend that combines:

- Retrieval-Augmented Generation (RAG)  
- OCR-powered document intelligence  
- Vector search with FAISS  
- Structured academic metadata storage  
- Teacher workflow automation  
- Adaptive student support  

It is designed to be modular, scalable, and deployable across schools and academic institutions.
```
