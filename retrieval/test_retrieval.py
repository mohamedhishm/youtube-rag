"""
Runs test questions against a sample video and writes test_results.md.

Usage:  python test_retrieval.py
Later, replace SAMPLE with real output from Karim's pipeline and rewrite the
expected chunk ids in TESTS to match.

A question passes when the expected chunk is in the top 2 results.
A "not in video" question passes when the best similarity is below
NOT_FOUND_THRESHOLD.
"""
import shutil
import sys

import retrieval as r

# Arabic text would crash the default Windows console, so force UTF-8 output.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Use a throwaway DB so tests never touch the real index.
r.CHROMA_PATH = "./chroma_test_db"
shutil.rmtree(r.CHROMA_PATH, ignore_errors=True)
r._collection = None

SAMPLE = {
    "video_id": "demo123",
    "title": "Introduction to RAG",
    "chunks": [
        {"chunk_id": "demo123_chunk_0", "start_seconds": 0.0, "end_seconds": 25.0,
         "text": "Large language models are trained on a fixed dataset, so they have a knowledge cutoff and know nothing about events after training."},
        {"chunk_id": "demo123_chunk_1", "start_seconds": 25.0, "end_seconds": 50.0,
         "text": "Models also hallucinate: they produce confident answers that sound right but are factually wrong, especially on private company data."},
        {"chunk_id": "demo123_chunk_2", "start_seconds": 50.0, "end_seconds": 80.0,
         "text": "Retrieval-Augmented Generation, or RAG, combines a retrieval step that finds relevant documents with a generation step where the model writes the answer from them."},
        {"chunk_id": "demo123_chunk_3", "start_seconds": 80.0, "end_seconds": 110.0,
         "text": "First we split documents into smaller chunks. A chunk size of around 500 tokens with some overlap keeps context while staying precise."},
        {"chunk_id": "demo123_chunk_4", "start_seconds": 110.0, "end_seconds": 140.0,
         "text": "Each chunk is converted into an embedding, a vector of numbers that captures its meaning. Similar meanings end up close together in vector space."},
        {"chunk_id": "demo123_chunk_5", "start_seconds": 140.0, "end_seconds": 170.0,
         "text": "The vectors are stored in a vector database such as Chroma, FAISS or Pinecone, which supports fast similarity search using cosine distance."},
        {"chunk_id": "demo123_chunk_6", "start_seconds": 170.0, "end_seconds": 200.0,
         "text": "At question time we embed the question, fetch the top-k most similar chunks, and put them into the prompt together with the question."},
        {"chunk_id": "demo123_chunk_7", "start_seconds": 200.0, "end_seconds": 230.0,
         "text": "Quality is measured with relevance, faithfulness and answer correctness. By the way, latency also matters when you add a re-ranking model."},
    ],
}

# (type, question, expected chunk id or None if the answer is NOT in the video)
TESTS = [
    ("direct",   "What is RAG?", "demo123_chunk_2"),
    ("direct",   "What chunk size is recommended?", "demo123_chunk_3"),
    ("direct",   "Which vector databases are mentioned?", "demo123_chunk_5"),
    ("synonym",  "Why do AI models make up false facts?", "demo123_chunk_1"),
    ("synonym",  "How do you turn text into numbers?", "demo123_chunk_4"),
    ("synonym",  "Why can't an LLM know recent news?", "demo123_chunk_0"),
    ("passing",  "Does latency matter?", "demo123_chunk_7"),
    ("passing",  "Is re-ranking mentioned?", "demo123_chunk_7"),
    ("missing",  "How do I bake chocolate cake?", None),
    ("missing",  "Who won the 2022 World Cup?", None),
    # Arabic questions about the English video (needs the multilingual model).
    ("arabic",   "ما هو الـ RAG؟", "demo123_chunk_2"),
    ("arabic",   "ما هو حجم الجزء المناسب عند تقسيم المستندات؟", "demo123_chunk_3"),
    ("arabic",   "لماذا تعطي النماذج إجابات خاطئة؟", "demo123_chunk_1"),
    ("arabic-missing", "كيف أطبخ الأرز؟", None),
]

NOT_FOUND_THRESHOLD = 0.20  # tune again after testing real videos


def main():
    n = r.index_chunks(SAMPLE)
    print(f"Model: {r.EMBEDDING_MODEL}")
    print(f"Indexed {n} chunks.\n")

    rows, passed = [], 0
    for kind, q, expected in TESTS:
        hits = r.retrieve_chunks("demo123", q, top_k=5)
        top = hits[0]
        ids = [h["chunk_id"] for h in hits]
        rank = ids.index(expected) + 1 if expected in ids else None
        if expected is None:
            ok = top["similarity"] < NOT_FOUND_THRESHOLD
        else:
            ok = rank is not None and rank <= 2  # top-2 counts
        passed += ok
        rows.append((kind, q, expected, top, rank, ok))
        rank_txt = "" if expected is None else f"  rank of expected={rank}"
        print(f"[{'PASS' if ok else 'FAIL'}] ({kind}) {q}\n"
              f"       top: {top['chunk_id']}  sim={top['similarity']}  "
              f"{top['start_seconds']}s-{top['end_seconds']}s{rank_txt}")

    # isolation check: a different video must never leak in
    other = dict(SAMPLE, video_id="other999",
                 chunks=[{"chunk_id": "other999_chunk_0", "start_seconds": 0, "end_seconds": 5,
                          "text": "Cooking pasta takes ten minutes in boiling salted water."}])
    r.index_chunks(other)
    leak = [h for h in r.retrieve_chunks("demo123", "How to cook pasta?", top_k=8)
            if h["video_id"] != "demo123"]
    iso_ok = not leak
    print(f"\n[{'PASS' if iso_ok else 'FAIL'}] isolation: no chunks from other videos")

    with open("test_results.md", "w", encoding="utf-8") as f:
        f.write(f"# Retrieval test results\n\nModel: `{r.EMBEDDING_MODEL}`  |  "
                f"Passed {passed}/{len(TESTS)}  |  isolation: {'PASS' if iso_ok else 'FAIL'}\n\n")
        f.write("| Type | Question | Expected | Top result | Similarity | Time | Rank of expected | Result |\n"
                "|---|---|---|---|---|---|---|---|\n")
        for kind, q, exp, top, rank, ok in rows:
            f.write(f"| {kind} | {q} | {exp or 'not in video'} | {top['chunk_id']} | "
                    f"{top['similarity']} | {top['start_seconds']}-{top['end_seconds']}s | "
                    f"{rank if exp else '-'} | {'PASS' if ok else 'FAIL'} |\n")
        f.write(f"\nAnswerable questions pass when the expected chunk is in the top 2. "
                f"'Not in video' passes when top similarity < {NOT_FOUND_THRESHOLD}.\n")
    print(f"\n{passed}/{len(TESTS)} passed. Saved test_results.md")


if __name__ == "__main__":
    main()
