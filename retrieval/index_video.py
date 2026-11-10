"""
Index one video's chunks from a JSON file, then ask questions in the terminal.

Usage:
    python index_video.py sample_video.json
    python index_video.py video1.json --top-k 3 --min-sim 0.20
    python index_video.py video1.json --ask "What is gradient descent?"

The JSON must follow Karim's contract:
    {"video_id": "...", "title": "...", "chunks": [
        {"chunk_id": "...", "text": "...", "start_seconds": 0.0, "end_seconds": 10.0}]}

Type 'q' to quit the question loop.
"""
import argparse
import json
import sys

import retrieval as r

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def fmt_time(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60}:{s % 60:02d}"


def show(results: list[dict], video_id: str) -> None:
    if not results:
        print("  -> No relevant chunk found (all scores below the threshold).")
        print("     The video probably does not answer this question.\n")
        return
    for i, h in enumerate(results, 1):
        link = f"https://www.youtube.com/watch?v={video_id}&t={int(h['start_seconds'])}s"
        print(f"  {i}. [{fmt_time(h['start_seconds'])}-{fmt_time(h['end_seconds'])}]"
              f"  sim={h['similarity']}  ({h['chunk_id']})")
        print(f"     {h['text']}")
        print(f"     {link}")
    print()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("json_file")
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--min-sim", type=float, default=0.20,
                   help="drop results below this similarity (use 0 to see everything)")
    p.add_argument("--ask", help="ask one question and exit")
    args = p.parse_args()

    with open(args.json_file, encoding="utf-8") as f:
        payload = json.load(f)

    print(f"Model: {r.EMBEDDING_MODEL}")
    n = r.index_chunks(payload)
    vid = payload["video_id"]
    print(f"Indexed {n} chunks for '{payload.get('title', vid)}' (video_id={vid}).\n")

    min_sim = args.min_sim if args.min_sim > 0 else None

    if args.ask:
        show(r.retrieve_chunks(vid, args.ask, args.top_k, min_sim), vid)
        return

    while True:
        q = input("Question (q to quit): ").strip()
        if q.lower() in ("q", "quit", "exit"):
            break
        if not q:
            continue
        try:
            show(r.retrieve_chunks(vid, q, args.top_k, min_sim), vid)
        except r.RetrievalError as e:
            print(f"  Error: {e}\n")


if __name__ == "__main__":
    main()
