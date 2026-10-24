
# YouTube Video RAG Assistant

A Python application for asking questions about YouTube
videos using their transcripts and Retrieval-Augmented Generation.

## Tech Stack

- Python
- FastAPI
- Pydantic
- ChromaDB (planned)
- Embeddings and an LLM (planned)

## Project Structure

- `app/`: FastAPI backend, API routes, schemas and services
- `transcript/`: Transcript extraction and chunking
- `retrieval/`: Embedding generation, indexing and retrieval
- `frontend/`: User interface
- `tests/`: Automated tests

## Setup

Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Run the API:

```powershell
uvicorn app.main:app --reload
```

Open the interactive API documentation at:

http://127.0.0.1:8000/docs

## Run Tests

```powershell
python -m pytest -v
```

## Development Status

The current API uses mock transcript and answer data.

Real transcript extraction, vector indexing, semantic
retrieval, and LLM answer generation will be integrated
as the team modules become available.

## Team Responsibilities

- Mohamed: Backend and integration
- Karim: Transcript pipeline
- Ali: Embeddings and retrieval
- Judy: Frontend
