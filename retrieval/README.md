# Retrieval Pipeline (Embeddings + ChromaDB)

Part of VideoMind AI. Takes Karim's chunks, stores them in ChromaDB, and returns the most relevant chunks for a question, **inside one video only**. No LLM is called here.

## Setup

Use **Python 3.12**. Python 3.15 is too new, and pip installs an old, broken ChromaDB on it.

```bash
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python test_retrieval.py
```

The first run downloads the embedding model (about 1.1 GB).

## Functions (`retrieval.py`)

| Function | Purpose |
|---|---|
| `index_chunks(payload)` | Embeds and stores a video's chunks. Re-indexing the same video replaces the old chunks. Returns the chunk count. |
| `retrieve_chunks(video_id, question, top_k=5, min_similarity=None)` | Top-K semantic search in that video only. Best match first. |
| `is_indexed(video_id)` | True if the video already has chunks stored. |
| `delete_video(video_id)` | Removes a video's chunks. |

### Input (Karim's contract)
```json
{"video_id": "abc123", "title": "Introduction to RAG",
 "chunks": [{"chunk_id": "abc123_chunk_0", "text": "...", "start_seconds": 35.0, "end_seconds": 58.0}]}
```

### Output of `retrieve_chunks`
```json
[{"chunk_id": "abc123_chunk_0", "video_id": "abc123", "text": "...",
  "start_seconds": 35.0, "end_seconds": 58.0, "similarity": 0.71}]
```
`similarity` is cosine similarity (higher is better). Pass `min_similarity=0.20` to drop weak matches. An empty list then means the video probably does not answer the question.

## Design choices

- **Embedding model (default):** `paraphrase-multilingual-mpnet-base-v2`. About 278M parameters, about 1.1 GB, 768 dimensions, runs on CPU with no GPU or API key. It puts Arabic and English in the same vector space, so it handles Arabic videos, mixed-language videos, and questions in a different language than the video.
- **English-only option:** `all-MiniLM-L6-v2` (22M parameters, about 90 MB, 384 dimensions). Smaller and faster. Use it with `set EMBEDDING_MODEL=all-MiniLM-L6-v2`.
- **After changing the model:** delete the `chroma_db` folder and index the videos again. Vectors from different models are not compatible.
- **ChromaDB:** persistent local folder (`CHROMA_PATH`, default `./chroma_db`), one collection, cosine space.
- **Metadata stored per chunk:** `video_id`, `title`, `chunk_id`, `start_seconds`, `end_seconds`.
- **Video isolation:** every query uses `where={"video_id": ...}`.

## Model comparison (sample English video, 10 questions)

| Model | Size | Result |
|---|---|---|
| all-MiniLM-L6-v2 | 22M, about 90 MB | 10/10 |
| paraphrase-multilingual-MiniLM-L12-v2 | 118M, about 470 MB | 9/10 (failed one vague paraphrase) |
| paraphrase-multilingual-mpnet-base-v2 | 278M, about 1.1 GB | 10/10 |

Typical similarity: correct chunks score about 0.35 to 0.73, and questions not in the video score about 0.10. The starting threshold `min_similarity=0.20` sits in that gap. Re-check it on real videos, because real transcripts are messier.

## Errors (`RetrievalError`)

- Payload missing `video_id`, empty `chunks`, or a chunk missing a field or with empty text.
- Empty question.
- Video not indexed yet. The backend should call `index_chunks` first.

## Tests

`python test_retrieval.py` runs 14 questions (direct, synonym, passing mention, Arabic, and not in video) plus a video-isolation check. It writes `test_results.md`, including the rank of the expected chunk. A question passes when the expected chunk is in the top 2. Swap the sample data for real output from Karim's pipeline before submitting the results.
