"""
Retriever service (Section 10.3): wraps Chroma querying for the live
request path. Domain filter is required — the router (Section 10.2)
always determines domain before this is called, per the Day 2 finding
that domain-filtered retrieval measurably outperforms unfiltered search.

Day 7 update: switched from sentence-transformers to fastembed (ONNX
Runtime backend) to avoid PyTorch's memory footprint, which exceeded
free-tier hosting's 512MB limit. Uses a quantized ONNX export of the
same intfloat/multilingual-e5-small model, sourced from Xenova's
standardized conversion (the official repo doesn't ship a quantized
variant). See Revision Log.
"""

from fastembed import TextEmbedding
from fastembed.common.model_description import PoolingType, ModelSource
import chromadb
from pathlib import Path

CHROMA_DB_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "govservice_docs"

MODEL_NAME = "xenova-e5-small-quantized"

TextEmbedding.add_custom_model(
    model=MODEL_NAME,
    pooling=PoolingType.MEAN,
    normalization=True,
    sources=ModelSource(hf="Xenova/multilingual-e5-small"),
    dim=384,
    model_file="onnx/model_quantized.onnx",
)

_model = TextEmbedding(model_name=MODEL_NAME)
_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
_collection = _client.get_collection(name=COLLECTION_NAME)


def retrieve(question: str, domain: str, n_results: int = 5) -> list[dict]:
    """
    Embed the question and return the top-n most similar chunks,
    filtered to the given domain.

    Returns a list of dicts: [{text, source_doc, distance}, ...]
    """
    prefixed_question = f"query: {question}"
    query_embedding = list(_model.embed([prefixed_question]))[0].tolist()

    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"domain": domain},
    )

    docs = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    return [
        {
            "text": doc,
            "source_doc": meta["source_doc"],
            "distance": dist,
        }
        for doc, meta, dist in zip(docs, metadatas, distances)
    ]