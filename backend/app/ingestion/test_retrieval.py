"""
Quick test: embed a question and query the Chroma collection to see
what comes back. Validates retrieval before we wire this into the
real router/retriever services (Day 3+).
"""

from sentence_transformers import SentenceTransformer
import chromadb
from pathlib import Path

CHROMA_DB_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "govservice_docs"

print("Loading embedding model...")
model = SentenceTransformer("intfloat/multilingual-e5-small")

print("Connecting to Chroma...")
client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
collection = client.get_collection(name=COLLECTION_NAME)

print(f"Collection has {collection.count()} chunks total.\n")


def search(question, n_results=3, domain_filter=None):
    """Embed a question and return the top-n most similar chunks."""
    # NOTE the "query: " prefix - required by e5 models on the QUESTION side,
    # matching the "passage: " prefix we used on the document side during ingestion.
    prefixed_question = f"query: {question}"
    query_embedding = model.encode(prefixed_question).tolist()

    where_clause = {"domain": domain_filter} if domain_filter else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_clause,
    )
    return results


def print_results(question, results):
    print(f"Q: {question}")
    docs = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for i, (doc, meta, dist) in enumerate(zip(docs, metadatas, distances)):
        print(f"\n  [{i+1}] domain={meta['domain']} | source={meta['source_doc']} | distance={dist:.4f}")
        print(f"      {doc[:150]}...")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    test_questions = [
        "How much does a 5 year passport cost?",
        "What documents do I need to correct my NID?",
        "What is the deadline to file income tax returns?",
        "What documents are needed for a new electricity connection?",
    ]

    for q in test_questions:
        results = search(q, n_results=3)
        print_results(q, results)

    # Domain-filtered retest of the question that failed above -
    # simulates what happens once the router has already picked a domain.
    print("--- DOMAIN-FILTERED RETEST ---\n")
    filtered_results = search("What documents do I need to correct my NID?", n_results=3, domain_filter="nid")
    print_results("What documents do I need to correct my NID? (filtered to domain=nid)", filtered_results)