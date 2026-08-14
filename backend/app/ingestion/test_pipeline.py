"""
Quick test: load one document, split header/body, chunk the body,
and embed the first chunk. This is a scratch script to validate the
concept before we build the real build_index.py.
"""

from sentence_transformers import SentenceTransformer

# ---- Step 1: Load the embedding model ----
# First run will download the model (~470MB) - only happens once, cached locally after.
print("Loading embedding model...")
model = SentenceTransformer("intfloat/multilingual-e5-small")
print(f"Model loaded. Max sequence length: {model.max_seq_length} tokens")

# ---- Step 2: Read one document and split header from body ----
test_file = "app/ingestion/documents/passport/fees.txt"

with open(test_file, "r", encoding="utf-8") as f:
    raw_text = f.read()

lines = raw_text.split("\n")
header_lines = [l for l in lines if l.strip().startswith("#")]
body_lines = [l for l in lines if not l.strip().startswith("#")]
body_text = "\n".join(body_lines).strip()

print(f"\nHeader fields found: {len(header_lines)}")
for h in header_lines:
    print(f"  {h}")
print(f"\nBody length: {len(body_text)} characters")

# ---- Step 3: Count tokens using the MODEL'S OWN tokenizer ----
tokenizer = model.tokenizer
token_count = len(tokenizer.encode(body_text))
print(f"\nFull body token count (model's tokenizer): {token_count} tokens")

# ---- Chunking function ----
def chunk_text(text, tokenizer, chunk_size=400, overlap=50):
    """
    Splits text into overlapping chunks, measured in the model's own tokens.
    - chunk_size: target tokens per chunk (we use 400, safely under the 512 limit,
      leaving headroom since the "passage: " prefix we add later also costs a few tokens)
    - overlap: tokens repeated between consecutive chunks, so a sentence that falls
      right on a chunk boundary still appears in full in at least one chunk
    """
    token_ids = tokenizer.encode(text, add_special_tokens=False)
    chunks = []
    start = 0
    while start < len(token_ids):
        end = start + chunk_size
        chunk_ids = token_ids[start:end]
        chunk_text_str = tokenizer.decode(chunk_ids)
        chunks.append(chunk_text_str)
        if end >= len(token_ids):
            break
        start = end - overlap  # step forward, but re-include the last `overlap` tokens
    return chunks

## ---- Step 4: Chunk the body and embed every chunk ----
chunks = chunk_text(body_text, tokenizer, chunk_size=400, overlap=50)
print(f"\nDocument split into {len(chunks)} chunk(s)")

for i, chunk in enumerate(chunks):
    chunk_token_count = len(tokenizer.encode(chunk, add_special_tokens=False))
    print(f"\n--- Chunk {i+1} ({chunk_token_count} tokens) ---")
    print(chunk[:150] + "..." if len(chunk) > 150 else chunk)

# Embed just the first chunk as a proof-of-concept
print("\nEmbedding chunk 1...")
prefixed_chunk = f"passage: {chunks[0]}"
embedding = model.encode(prefixed_chunk)
print(f"Embedding generated. Shape: {embedding.shape}")