"""
build_index.py

Walks all four domain folders under documents/, chunks every source file,
embeds each chunk, and stores everything in a plain JSON file for the
lightweight in-memory retriever (Day 7 - replaced chromadb, see
Revision Log).

Run manually whenever source documents change (Section 10.1) - not part
of the live request path.
"""

import json
from pathlib import Path
from fastembed import TextEmbedding
from fastembed.common.model_description import PoolingType, ModelSource
from tokenizers import Tokenizer

DOCUMENTS_DIR = Path(__file__).parent / "documents"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "index.json"

MODEL_NAME = "xenova-e5-small-quantized"
HF_REPO = "Xenova/multilingual-e5-small"

CHUNK_SIZE = 400   # tokens, measured by the embedding model's own tokenizer
CHUNK_OVERLAP = 50


def parse_document(filepath):
    """Reads one .txt file and splits it into (metadata_dict, body_text)."""
    with open(filepath, "r", encoding="utf-8") as f:
        raw_text = f.read()

    lines = raw_text.split("\n")
    header_lines = [l for l in lines if l.strip().startswith("#")]
    body_lines = [l for l in lines if not l.strip().startswith("#")]
    body_text = "\n".join(body_lines).strip()

    metadata = {}
    for line in header_lines:
        content = line.strip().lstrip("#").strip()
        if ":" in content:
            key, value = content.split(":", 1)
            metadata[key.strip()] = value.strip()

    return metadata, body_text


def chunk_text(text, tokenizer, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Splits text into overlapping chunks, measured in the model's own tokens."""
    token_ids = tokenizer.encode(text, add_special_tokens=False).ids
    if not token_ids:
        return []
    chunks = []
    start = 0
    while start < len(token_ids):
        end = start + chunk_size
        chunk_ids = token_ids[start:end]
        chunks.append(tokenizer.decode(chunk_ids))
        if end >= len(token_ids):
            break
        start = end - overlap
    return chunks


def discover_documents(documents_dir):
    """
    Walks the documents/ folder and returns a list of (filepath, domain) pairs.
    domain = the top-level folder name under documents/ (passport, nid, tax, utilities).
    """
    results = []
    for filepath in documents_dir.rglob("*.txt"):
        relative = filepath.relative_to(documents_dir)
        domain = relative.parts[0]
        results.append((filepath, domain))
    return results


def build_index():
    """Full pipeline: discover -> parse -> chunk -> embed -> save as JSON."""

    print("Loading embedding model...")
    TextEmbedding.add_custom_model(
        model=MODEL_NAME,
        pooling=PoolingType.MEAN,
        normalization=True,
        sources=ModelSource(hf=HF_REPO),
        dim=384,
        model_file="onnx/model_quantized.onnx",
    )
    model = TextEmbedding(model_name=MODEL_NAME)
    tokenizer = Tokenizer.from_pretrained(HF_REPO)

    docs = discover_documents(DOCUMENTS_DIR)
    print(f"Found {len(docs)} document(s). Processing...")

    all_chunks = []

    for filepath, domain in docs:
        metadata, body_text = parse_document(filepath)
        chunks = chunk_text(body_text, tokenizer)
        source_doc_name = filepath.stem

        for i, chunk in enumerate(chunks):
            prefixed_chunk = f"passage: {chunk}"
            embedding = list(model.embed([prefixed_chunk]))[0]

            all_chunks.append({
                "id": f"{domain}__{source_doc_name}__{i}",
                "domain": domain,
                "source_doc": source_doc_name,
                "section": metadata.get("section", ""),
                "language": metadata.get("language", ""),
                "source_url": metadata.get("source_url", ""),
                "text": chunk,
                "embedding": embedding.tolist(),
            })

        print(f"  {domain}/{source_doc_name}: {len(chunks)} chunk(s)")

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False)

    print(f"\nDone. Saved {len(all_chunks)} chunk(s) to {OUTPUT_PATH}.")


if __name__ == "__main__":
    build_index()