"""
VideoMind AI - Retrieval Pipeline (Ali)

Takes the chunk JSON produced by the Transcript Pipeline (Karim), embeds the
chunks, stores them in ChromaDB, and retrieves the most relevant chunks for a
question, restricted to ONE video. No LLM is called here.

Input contract (from Karim):
{
  "video_id": "abc123",
  "title": "Introduction to RAG",
  "chunks": [
    {"chunk_id": "abc123_chunk_0", "text": "...", "start_seconds": 35.0, "end_seconds": 58.0}
  ]
}

Output of retrieve_chunks():
[
  {"chunk_id": "...", "video_id": "...", "text": "...",
   "start_seconds": 35.0, "end_seconds": 58.0, "similarity": 0.71},
  ...
]
"""

import os
import re
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------- config ----
# Default: multilingual (Arabic + English, ~278M params, ~1.1 GB, 768 dims,
# runs on CPU). Passed 10/10 on the English test set.
# For English-only videos a smaller option is:
#   EMBEDDING_MODEL=all-MiniLM-L6-v2   (22M params, ~90 MB, 384 dims)
# Vectors from different models are NOT compatible, so each model gets its own
# collection automatically (see COLLECTION_NAME below).
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-mpnet-base-v2")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
# One collection per embedding model: vectors from different models have
# different sizes (768 vs 384) and cannot share a collection.
# Chroma names: 3-63 chars, letters/digits/._- only, start/end alphanumeric.
COLLECTION_NAME = (
    "video_chunks_" + re.sub(r"[^A-Za-z0-9_-]", "_", EMBEDDING_MODEL)
)[:63].rstrip("_-")

_model: Optional[SentenceTransformer] = None
_collection = None


class RetrievalError(Exception):
    """Raised for invalid input or when a video has not been indexed."""


# --------------------------------------------------------------- internals --
def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        # cosine space => distance = 1 - cosine_similarity
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
    return _collection


def _embed(texts: list[str]) -> list[list[float]]:
    return _get_model().encode(
        texts, normalize_embeddings=True, show_progress_bar=False
    ).tolist()


def _validate_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        raise RetrievalError("Payload must be a dict.")
    if not payload.get("video_id"):
        raise RetrievalError("Payload is missing 'video_id'.")
    chunks = payload.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise RetrievalError("Payload has no chunks to index.")
    for i, c in enumerate(chunks):
        for key in ("chunk_id", "text", "start_seconds", "end_seconds"):
            if key not in c:
                raise RetrievalError(f"Chunk #{i} is missing '{key}'.")
        if not str(c["text"]).strip():
            raise RetrievalError(f"Chunk #{i} has empty text.")


# ------------------------------------------------------------- public API ---
def index_chunks(payload: dict) -> int:
    """
    Embed and store all chunks of one video. Safe to call twice for the same
    video: old chunks are removed first, so there are no duplicates.
    Returns the number of chunks indexed.
    """
    _validate_payload(payload)
    video_id = payload["video_id"]
    title = payload.get("title") or ""
    chunks = payload["chunks"]

    col = _get_collection()
    col.delete(where={"video_id": video_id})  # re-index = replace

    texts = [c["text"] for c in chunks]
    col.add(
        ids=[c["chunk_id"] for c in chunks],
        documents=texts,
        embeddings=_embed(texts),
        metadatas=[
            {
                "video_id": video_id,
                "title": title,
                "chunk_id": c["chunk_id"],
                "start_seconds": float(c["start_seconds"]),
                "end_seconds": float(c["end_seconds"]),
            }
            for c in chunks
        ],
    )
    return len(chunks)


def is_indexed(video_id: str) -> bool:
    res = _get_collection().get(where={"video_id": video_id}, limit=1)
    return len(res["ids"]) > 0


def delete_video(video_id: str) -> None:
    _get_collection().delete(where={"video_id": video_id})


def retrieve_chunks(
    video_id: str,
    question: str,
    top_k: int = 5,
    min_similarity: Optional[float] = None,
) -> list[dict]:
    """
    Semantic search inside ONE video.
    - Results are sorted best-first.
    - similarity is cosine similarity (higher = more related, roughly 0..1).
    - If min_similarity is set, weaker matches are dropped, so an empty list
      means "the video probably doesn't answer this".
    """
    if not question or not question.strip():
        raise RetrievalError("Question is empty.")
    if not is_indexed(video_id):
        raise RetrievalError(f"Video '{video_id}' is not indexed yet.")

    res = _get_collection().query(
        query_embeddings=_embed([question]),
        n_results=top_k,
        where={"video_id": video_id},  # never leaks other videos
    )

    results = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        sim = round(1.0 - dist, 4)
        if min_similarity is not None and sim < min_similarity:
            continue
        results.append(
            {
                "chunk_id": meta["chunk_id"],
                "video_id": meta["video_id"],
                "text": doc,
                "start_seconds": meta["start_seconds"],
                "end_seconds": meta["end_seconds"],
                "similarity": sim,
            }
        )
    return results
