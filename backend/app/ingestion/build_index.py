"""
build_index.py

Walks all four domain folders under documents/, chunks every source file,
embeds each chunk, and stores everything in a persistent Chroma collection.

Run manually whenever source documents change (Section 10.1) - not part of
the live request path.
"""

import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

DOCUMENTS_DIR = Path(__file__).parent / "documents"
CHROMA_DB_DIR = Path(__file__).parent.parent / "chroma_db"  # persisted DB lives in app/chroma_db
COLLECTION_NAME = "govservice_docs"

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
        # format: "# key: value"
        content = line.strip().lstrip("#").strip()
        if ":" in content:
            key, value = content.split(":", 1)
            metadata[key.strip()] = value.strip()

    return metadata, body_text


def chunk_text(text, tokenizer, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Splits text into overlapping chunks, measured in the model's own tokens."""
    token_ids = tokenizer.encode(text, add_special_tokens=False)
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
    Files inside nested subfolders (e.g. utilities/gas/) still get domain="utilities"
    - only the FIRST folder level under documents/ counts as the domain.
    """
    results = []
    for filepath in documents_dir.rglob("*.txt"):
        relative = filepath.relative_to(documents_dir)
        domain = relative.parts[0]  # first folder = domain
        results.append((filepath, domain))
    return results


def build_index():
    """Full pipeline: discover -> parse -> chunk -> embed -> store in Chroma."""

    print("Loading embedding model...")
    model = SentenceTransformer("intfloat/multilingual-e5-small")
    tokenizer = model.tokenizer

    print("Connecting to Chroma...")
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    # get_or_create so re-running this script doesn't error if the collection already exists
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    docs = discover_documents(DOCUMENTS_DIR)
    print(f"Found {len(docs)} document(s). Processing...")

    all_ids = []
    all_embeddings = []
    all_metadatas = []
    all_documents = []  # the chunk text itself, so Chroma can return it on retrieval

    for filepath, domain in docs:
        metadata, body_text = parse_document(filepath)
        chunks = chunk_text(body_text, tokenizer)

        source_doc_name = filepath.stem  # filename without .txt extension

        for i, chunk in enumerate(chunks):
            chunk_id = f"{domain}__{source_doc_name}__{i}"

            chunk_metadata = {
                "domain": domain,
                "source_doc": source_doc_name,
                "section": metadata.get("section", ""),
                "language": metadata.get("language", ""),
                "source_url": metadata.get("source_url", ""),
            }

            prefixed_chunk = f"passage: {chunk}"
            embedding = model.encode(prefixed_chunk)

            all_ids.append(chunk_id)
            all_embeddings.append(embedding.tolist())
            all_metadatas.append(chunk_metadata)
            all_documents.append(chunk)

        print(f"  {domain}/{source_doc_name}: {len(chunks)} chunk(s)")

    print(f"\nUpserting {len(all_ids)} chunks into Chroma...")
    collection.upsert(
        ids=all_ids,
        embeddings=all_embeddings,
        metadatas=all_metadatas,
        documents=all_documents,
    )

    print(f"Done. Collection '{COLLECTION_NAME}' now has {collection.count()} chunk(s).")


if __name__ == "__main__":
    build_index()