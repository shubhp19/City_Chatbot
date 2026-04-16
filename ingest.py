"""
City Data Ingestion Pipeline
Loads city_data.json, chunks it, embeds, and stores in ChromaDB.
Run once after data_loader.py.
"""

import json
import re
import chromadb
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_PATH       = "city_data.json"
CHROMA_DB_PATH  = "./chroma_db"
COLLECTION_NAME = "syracuse_city"
EMBED_MODEL     = "all-MiniLM-L6-v2"
CHUNK_SIZE      = 600
CHUNK_OVERLAP   = 120


def chunk_text(text: str) -> list[str]:
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    chunks, start = [], 0
    while start < len(text):
        chunk = text[start:start + CHUNK_SIZE].strip()
        if len(chunk) > 60:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def ingest():
    logger.info("Loading city data...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        documents = json.load(f)
    logger.info(f"Loaded {len(documents)} documents.")

    logger.info(f"Loading embedding model: {EMBED_MODEL}")
    embedder = SentenceTransformer(EMBED_MODEL)

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    all_docs, all_ids, all_metas = [], [], []

    for i, doc in enumerate(documents):
        title    = doc.get("title", "")
        content  = doc.get("content", "")
        category = doc.get("category", "")
        source   = doc.get("source", "")
        full     = f"Title: {title}\nCategory: {category}\nSource: {source}\n\n{content}"

        for j, chunk in enumerate(chunk_text(full)):
            all_docs.append(chunk)
            all_ids.append(f"doc_{i}_chunk_{j}")
            all_metas.append({
                "title": title,
                "category": category,
                "source": source,
                "chunk_index": j
            })

    logger.info(f"Generated {len(all_docs)} chunks. Embedding & storing...")

    BATCH = 128
    for i in range(0, len(all_docs), BATCH):
        b_docs  = all_docs[i:i+BATCH]
        b_ids   = all_ids[i:i+BATCH]
        b_metas = all_metas[i:i+BATCH]
        embeds  = embedder.encode(b_docs, show_progress_bar=False).tolist()
        collection.add(documents=b_docs, embeddings=embeds,
                       ids=b_ids, metadatas=b_metas)
        logger.info(f"  Stored {min(i+BATCH, len(all_docs))}/{len(all_docs)}")

    logger.info(f"✅ Done! {len(all_docs)} chunks stored in ChromaDB.")


if __name__ == "__main__":
    ingest()
