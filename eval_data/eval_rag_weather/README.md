# Eval dataset for RAGAS (weather agent RAG)

Folder: eval_data/eval_rag_weather (to avoid name clash with HuggingFace `datasets`).

Used by RAG evaluation to compute faithfulness, answer_relevancy, context_precision, context_recall.

- `dataset.py`: builds HuggingFace Dataset with question, contexts, answer, ground_truth.
- Samples are in Ukrainian; ground_truth describes expected content (recommendation + optional historical comparison).
