"""
Test the Retrieval module on a REAL YouTube video.

Put this file in the ROOT of the youtube-rag repo (next to the `transcript`
and `retrieval` folders), then run from that folder:

    python demo_real_video.py "https://www.youtube.com/watch?v=VIDEO_ID"

Optional: preferred languages (comma separated), e.g. ar,en
    python demo_real_video.py "https://www.youtube.com/watch?v=VIDEO_ID" ar,en

What it does:
 1. Runs Karim's pipeline  -> saves <video_id>.json
 2. Indexes the chunks     -> your retrieval module (ChromaDB)
 3. Asks questions         -> from questions.txt (one per line, UTF-8) if that
                              file exists, otherwise you type them
 4. Logs every answer      -> real_video_results.md (for your report)
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
# Put the retrieval FOLDER first so `import retrieval` finds retrieval.py
sys.path.insert(0, os.path.join(HERE, "retrieval"))
sys.path.insert(1, HERE)

import retrieval as r  # noqa: E402
from transcript.pipeline import process_youtube_video  # noqa: E402

MIN_SIMILARITY = 0.20  # below this the answer is probably not in the video
TOP_K = 5
RESULTS_FILE = "real_video_results.md"


def yt_link(video_id: str, start: float) -> str:
    return f"https://www.youtube.com/watch?v={video_id}&t={int(start)}s"


def ask(video_id: str, question: str, log) -> None:
    hits = r.retrieve_chunks(video_id, question, top_k=TOP_K)
    print(f"\nQ: {question}")
    if hits[0]["similarity"] < MIN_SIMILARITY:
        print("   (best score is low: the video probably does NOT answer this)")
    log.write(f"\n## Q: {question}\n\n")
    log.write("| Rank | Similarity | Time | Link | Text (start) |\n|---|---|---|---|---|\n")
    for i, h in enumerate(hits, 1):
        t = f"{h['start_seconds']:.0f}s-{h['end_seconds']:.0f}s"
        link = yt_link(video_id, h["start_seconds"])
        snippet = h["text"][:140].replace("|", "/").replace("\n", " ")
        print(f"  {i}. sim={h['similarity']}  {t}  {link}\n     {snippet}")
        log.write(f"| {i} | {h['similarity']} | {t} | {link} | {snippet} |\n")
    log.write("\nRelevant? (fill in: yes / no / partly): \n")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        return
    url = sys.argv[1]
    langs = sys.argv[2].split(",") if len(sys.argv) > 2 else None

    print("Step 1: running Karim's transcript pipeline...")
    result = process_youtube_video(url, preferred_languages=langs)
    if result.get("status") != "success":
        err = result.get("error") or {}
        print(f"FAILED: {err.get('code')} - {err.get('message')}")
        print("Try another video, or check the error code with Karim.")
        return

    video_id = result["video_id"]
    with open(f"{video_id}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    chunks = result["chunks"]
    print(f"  OK: {len(chunks)} chunks, language={result.get('transcript_language')}, "
          f"saved {video_id}.json")

    print("Step 2: indexing with the retrieval module (first run loads the model)...")
    try:
        n = r.index_chunks(result)
    except r.RetrievalError as e:
        print(f"INDEX ERROR: {e}")
        print("First chunk keys from Karim:", list(chunks[0].keys()))
        print("My module needs: chunk_id, text, start_seconds, end_seconds")
        return
    print(f"  OK: indexed {n} chunks")

    print("Step 3: questions")
    with open(RESULTS_FILE, "a", encoding="utf-8") as log:
        log.write(f"\n# Video {video_id}  (model: {r.EMBEDDING_MODEL}, "
                  f"{len(chunks)} chunks)\n")
        if os.path.exists("questions.txt"):
            with open("questions.txt", encoding="utf-8") as f:
                questions = [q.strip() for q in f if q.strip()]
            for q in questions:
                ask(video_id, q, log)
        else:
            print("(no questions.txt found: type questions, empty line to quit)")
            while True:
                q = input("\nQuestion: ").strip()
                if not q:
                    break
                ask(video_id, q, log)
    print(f"\nDone. Results saved in {RESULTS_FILE}")


if __name__ == "__main__":
    main()
