# YouTube Video RAG Assistant

An AI-powered assistant that allows users to ask questions about YouTube videos and receive answers grounded in video transcripts, with source excerpts and timestamps.

> **Development status:** The backend API is implemented and tested. Transcript processing and retrieval currently use mock data while the team integrates the real transcript pipeline, semantic retriever, and frontend.

## Project Overview

The goal is to build a Retrieval-Augmented Generation (RAG) system that:

1. Accepts a YouTube video URL.
2. Extracts and processes the video's transcript.
3. Splits the transcript into timestamped chunks.
4. Retrieves relevant chunks for a user's question.
5. Generates a grounded answer using an LLM.
6. Returns the answer with source excerpts and timestamps.

## Tech Stack

- Python
- FastAPI
- Pydantic
- Groq API for LLM inference
- ChromaDB and embeddings — planned for semantic retrieval
- Pytest for API testing

## Current Features

- FastAPI application with interactive Swagger documentation.
- YouTube URL validation and video ID extraction.
- Video processing and status endpoints.
- Question-and-answer endpoint.
- Structured response schemas for transcript chunks and sources.
- Temporary in-memory video storage.
- Mock transcript data for backend development.
- Optional Groq-powered answer generation.
- API tests covering health checks, video processing, status, timestamps, invalid URLs, and missing videos.

## Project Structure

```text
youtube-rag/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── core/
│   │   └── config.py
│   ├── schemas/
│   │   └── models.py
│   └── services/
│       ├── video_service.py
│       └── rag_service.py
├── tests/
│   └── test_api.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/mohamedhishm/youtube-rag.git
cd youtube-rag
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Configure the following variables in `.env`:

```dotenv
APP_NAME=YouTube Video RAG Assistant
DEBUG=true
MOCK_MODE=true
USE_LLM=false
GROQ_API_KEY=
```

To enable Groq-powered answers, add your own Groq API key and set `USE_LLM=true`.

**Never commit `.env` or expose API keys in source code, logs, screenshots, or GitHub.**

### 5. Run the tests

For the current mock-based tests, set `USE_LLM=false` in `.env` first.

```powershell
python -m pytest -v
```

### 6. Start the API server

```powershell
uvicorn app.main:app --reload
```

Open the interactive API documentation:

http://127.0.0.1:8000/docs

Health check:

http://127.0.0.1:8000/health

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API welcome message |
| GET | `/health` | Health check |
| POST | `/api/videos/process` | Process a video URL |
| GET | `/api/videos/{video_id}/status` | Retrieve video status |
| POST | `/api/videos/{video_id}/questions` | Ask a question about a video |

### Example: Process a video

`POST /api/videos/process`

```json
{
  "url": "https://www.youtube.com/watch?v=abcdefghijk"
}
```

### Example: Ask a question

`POST /api/videos/abcdefghijk/questions`

```json
{
  "question": "What is RAG?",
  "top_k": 2
}
```

The response includes an answer and a list of source chunks with their timestamps.

## Team Responsibilities

- **Mohamed:** Backend API, application configuration, service integration, and overall backend coordination.
- **Karim:** YouTube transcript extraction, cleaning, and timestamp-preserving chunking.
- **Ali:** Embeddings, ChromaDB indexing, and semantic retrieval.
- **Judi:** Frontend interface and API integration.

The team should coordinate shared schemas and interfaces before integrating modules.

## Current Limitations

- Video processing currently uses mock transcript data; it does not yet retrieve a real YouTube transcript.
- Retrieval currently selects the first available chunks rather than performing semantic search.
- Groq generation is optional and must be configured locally.
- Video state is stored in memory and is lost when the server restarts.
- The complete RAG pipeline and frontend integration are still in development.

## Security

- Keep `.env` out of version control.
- Use `.env.example` to document required environment variables without real credentials.
- Never commit API keys or other secrets.

## License

To be determined.
