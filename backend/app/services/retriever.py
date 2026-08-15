"""
Retriever service (Section 10.3): lightweight in-memory search over a
plain JSON export of the document collection, replacing chromadb (Day 7
- see Revision Log). Domain filter is required - the router (Section
10.2) always determines domain before this is called, per the Day 2
finding that domain-filtered retrieval measurably outperforms
unfiltered search.

Distance metric: squared L2 (Euclidean), matching chromadb's default
"l2" space - preserves distance-scale compatibility with
services/confidence.py's existing DISTANCE_THRESHOLD, tuned against
values observed under that same metric.
"""

import json
import numpy as np
from pathlib import Path
from fastembed import TextEmbedding
from fastembed.common.model_description import PoolingType, ModelSource

DATA_PATH = Path(__file__).parent.parent / "data" / "index.json"

MODEL_NAME = "xenova-e5-small-quantized"

TextEmbedding.add_custom_model(
    model=MODEL_NAME,
    pooling=PoolingType.MEAN,
    normalization=True,
    sources=ModelSource(hf="Xenova/multilingual-e5-small"),
    dim=384,
    model_file="onnx/model_quantized.onnx",
)

_model = TextEmbedding(
    model_name=MODEL_NAME,
    providers=["CPUExecutionProvider"],
    session_options={"enable_cpu_mem_arena": False, "enable_mem_pattern": False},
)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    _chunks = json.load(f)

_embeddings = np.array([c["embedding"] for c in _chunks], dtype=np.float32)


def retrieve(question: str, domain: str, n_results: int = 5) -> list[dict]:
    """
    Embed the question and return the top-n most similar chunks,
    filtered to the given domain.

    Returns a list of dicts: [{text, source_doc, distance}, ...]
    """
    prefixed_question = f"query: {question}"
    query_embedding = np.array(list(_model.embed([prefixed_question]))[0], dtype=np.float32)

    domain_indices = [i for i, c in enumerate(_chunks) if c["domain"] == domain]
    if not domain_indices:
        return []

    domain_embeddings = _embeddings[domain_indices]
    diffs = domain_embeddings - query_embedding
    distances = np.sum(diffs ** 2, axis=1)

    order = np.argsort(distances)[:n_results]

    results = []
    for idx in order:
        chunk_idx = domain_indices[idx]
        results.append({
            "text": _chunks[chunk_idx]["text"],
            "source_doc": _chunks[chunk_idx]["source_doc"],
            "distance": float(distances[idx]),
        })
    return results