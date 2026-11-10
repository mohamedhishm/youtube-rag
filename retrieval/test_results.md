# Retrieval test results

Model: `paraphrase-multilingual-mpnet-base-v2`  |  Passed 14/14  |  isolation: PASS

| Type | Question | Expected | Top result | Similarity | Time | Rank of expected | Result |
|---|---|---|---|---|---|---|---|
| direct | What is RAG? | demo123_chunk_2 | demo123_chunk_2 | 0.4962 | 50.0-80.0s | 1 | PASS |
| direct | What chunk size is recommended? | demo123_chunk_3 | demo123_chunk_3 | 0.4208 | 80.0-110.0s | 1 | PASS |
| direct | Which vector databases are mentioned? | demo123_chunk_5 | demo123_chunk_5 | 0.5471 | 140.0-170.0s | 1 | PASS |
| synonym | Why do AI models make up false facts? | demo123_chunk_1 | demo123_chunk_1 | 0.73 | 25.0-50.0s | 1 | PASS |
| synonym | How do you turn text into numbers? | demo123_chunk_4 | demo123_chunk_3 | 0.3629 | 80.0-110.0s | 2 | PASS |
| synonym | Why can't an LLM know recent news? | demo123_chunk_0 | demo123_chunk_1 | 0.3497 | 25.0-50.0s | 2 | PASS |
| passing | Does latency matter? | demo123_chunk_7 | demo123_chunk_7 | 0.5963 | 200.0-230.0s | 1 | PASS |
| passing | Is re-ranking mentioned? | demo123_chunk_7 | demo123_chunk_7 | 0.482 | 200.0-230.0s | 1 | PASS |
| missing | How do I bake chocolate cake? | not in video | demo123_chunk_3 | 0.103 | 80.0-110.0s | - | PASS |
| missing | Who won the 2022 World Cup? | not in video | demo123_chunk_6 | 0.1024 | 170.0-200.0s | - | PASS |
| arabic | ما هو الـ RAG؟ | demo123_chunk_2 | demo123_chunk_2 | 0.4741 | 50.0-80.0s | 1 | PASS |
| arabic | ما هو حجم الجزء المناسب عند تقسيم المستندات؟ | demo123_chunk_3 | demo123_chunk_3 | 0.5825 | 80.0-110.0s | 1 | PASS |
| arabic | لماذا تعطي النماذج إجابات خاطئة؟ | demo123_chunk_1 | demo123_chunk_1 | 0.6017 | 25.0-50.0s | 1 | PASS |
| arabic-missing | كيف أطبخ الأرز؟ | not in video | demo123_chunk_3 | 0.0625 | 80.0-110.0s | - | PASS |

Answerable questions pass when the expected chunk is in the top 2. 'Not in video' passes when top similarity < 0.2.
