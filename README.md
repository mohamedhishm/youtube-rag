Use Python 3.12 (3.15 breaks ChromaDB).

1) python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
2) Create a file named .env next to requirements.txt:
     MOCK_MODE=false
     USE_LLM=false
   (MOCK_MODE=true = fake data, no model download.)
3) Backend (window 1):   uvicorn app.main:app --reload
4) Frontend (window 2):  cd frontend
                         python -m http.server 5500
5) Open http://localhost:5500 and use a video that HAS captions.

First real video: the embedding model (~1.1 GB) downloads once.
Process video can take a few minutes the first time.
