"""
Syracuse City Chatbot Engine
Groq API + ChromaDB RAG
Roles: Resident and City Official
"""

import chromadb
from groq import Groq
from sentence_transformers import SentenceTransformer
import json
import os
from datetime import datetime

CHROMA_DB_PATH  = "./chroma_db"
COLLECTION_NAME = "syracuse_city"
EMBED_MODEL     = "all-MiniLM-L6-v2"
GROQ_MODEL      = "llama-3.3-70b-versatile"
TOP_K           = 6
ANNOUNCEMENTS_FILE = "announcements.json"

RESIDENT_PROMPT = """You are a helpful AI assistant for the City of Syracuse, New York.
You help RESIDENTS with:
- Finding city services and how to access them
- Understanding housing code, lead paint risk, and violations
- Locating parks, recreation programs, and community events
- Learning about neighborhood resources and organizations
- How to report issues (311, code violations, etc.)
- Understanding city data about their neighborhood

Tone: Warm, clear, accessible. Many residents may be dealing with difficult housing or health situations.
Rules:
- Answer based on the provided context
- Always include actionable next steps (phone numbers, websites, addresses)
- If unsure, direct to 311 or the relevant city department
- Never minimize housing or health concerns — take them seriously
- Respond in simple, plain language — avoid jargon"""

OFFICIAL_PROMPT = """You are an AI assistant for City of Syracuse government officials and staff.
You help CITY OFFICIALS with:
- Analyzing patterns in housing violations, lead risk, and 311 requests
- Understanding neighborhood-level data and trends
- Identifying high-risk areas and resource allocation needs
- Accessing data about vacant properties, demolitions, businesses
- Understanding city service performance and gaps
- Supporting data-driven policy and planning decisions

Tone: Professional, analytical, data-focused.
Rules:
- Answer based on the provided context and data
- Highlight patterns, trends, and geographic concentrations when relevant
- Reference specific data counts and statistics from context
- Flag data limitations and caveats
- Suggest actionable insights for policy or resource allocation"""


class AnnouncementManager:
    def __init__(self, filepath=ANNOUNCEMENTS_FILE):
        self.filepath = filepath
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                self.data = json.load(f)
        else:
            self.data = []

    def _save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.data, f, indent=2)

    def post(self, author: str, category: str, title: str, body: str) -> dict:
        ann = {
            "id": len(self.data) + 1,
            "author": author,
            "category": category,
            "title": title,
            "body": body,
            "posted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "active": True
        }
        self.data.append(ann)
        self._save()
        return ann

    def get_all(self, active_only=True) -> list:
        return [a for a in self.data if a.get("active", True)] if active_only else self.data

    def delete(self, ann_id: int) -> bool:
        for a in self.data:
            if a["id"] == ann_id:
                a["active"] = False
                self._save()
                return True
        return False

    def edit(self, ann_id: int, title: str = None, body: str = None) -> bool:
        for a in self.data:
            if a["id"] == ann_id and a.get("active", True):
                if title: a["title"] = title
                if body:  a["body"] = body
                a["edited_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                self._save()
                return True
        return False


class SyracuseCityChatbot:
    def __init__(self, api_key: str, role: str = "resident"):
        self.role = role.lower()
        self.client = Groq(api_key=api_key)
        self.announcements = AnnouncementManager()

        print("Loading embedding model...")
        self.embedder = SentenceTransformer(EMBED_MODEL)

        print("Connecting to ChromaDB...")
        db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        try:
            self.collection = db.get_collection(COLLECTION_NAME)
        except Exception:
            print("Collection not found — building knowledge base from scratch...")
            self._build_db(db)
            self.collection = db.get_collection(COLLECTION_NAME)
        print(f"✅ Ready [{self.role.upper()} mode] — {self.collection.count()} chunks loaded.")

        self.history = []

    def _build_db(self, db):
        """Download city data and build ChromaDB collection from scratch."""
        import re
        from data_loader import load_all

        print("Downloading Syracuse city data...")
        documents = load_all()

        collection = db.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        CHUNK_SIZE, CHUNK_OVERLAP, BATCH = 600, 120, 128
        all_docs, all_ids, all_metas = [], [], []

        for i, doc in enumerate(documents):
            title    = doc.get("title", "")
            content  = doc.get("content", "")
            category = doc.get("category", "")
            source   = doc.get("source", "")
            full     = f"Title: {title}\nCategory: {category}\nSource: {source}\n\n{content}"
            full     = re.sub(r'\n{3,}', '\n\n', full).strip()

            start = 0
            j = 0
            while start < len(full):
                chunk = full[start:start + CHUNK_SIZE].strip()
                if len(chunk) > 60:
                    all_docs.append(chunk)
                    all_ids.append(f"doc_{i}_chunk_{j}")
                    all_metas.append({"title": title, "category": category,
                                      "source": source, "chunk_index": j})
                    j += 1
                start += CHUNK_SIZE - CHUNK_OVERLAP

        print(f"Embedding {len(all_docs)} chunks...")
        for i in range(0, len(all_docs), BATCH):
            b_docs  = all_docs[i:i+BATCH]
            b_ids   = all_ids[i:i+BATCH]
            b_metas = all_metas[i:i+BATCH]
            embeds  = self.embedder.encode(b_docs, show_progress_bar=False).tolist()
            collection.add(documents=b_docs, embeddings=embeds,
                           ids=b_ids, metadatas=b_metas)
        print(f"✅ Knowledge base built — {len(all_docs)} chunks stored.")

    @property
    def system_prompt(self):
        return RESIDENT_PROMPT if self.role == "resident" else OFFICIAL_PROMPT

    def retrieve(self, query: str) -> list[dict]:
        embedding = self.embedder.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=embedding,
            n_results=TOP_K,
            include=["documents", "metadatas", "distances"]
        )
        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            chunks.append({
                "content": doc,
                "title":    meta.get("title", ""),
                "category": meta.get("category", ""),
                "source":   meta.get("source", ""),
                "score":    round(1 - dist, 3)
            })
        return chunks

    def build_context(self, chunks: list[dict]) -> str:
        parts = []
        for i, c in enumerate(chunks, 1):
            parts.append(
                f"[Source {i}: {c['title']} | {c['category']}]\n{c['content']}\nURL: {c['source']}"
            )
        return "\n\n---\n\n".join(parts)

    def chat(self, user_message: str) -> dict:
        chunks  = self.retrieve(user_message)
        context = self.build_context(chunks)

        ann_context = ""
        if self.role == "resident":
            active = self.announcements.get_all()
            if active:
                ann_lines = [
                    f"- [{a['category']}] {a['title']}: {a['body']} (Posted {a['posted_at']})"
                    for a in active[-5:]
                ]
                ann_context = "\n\nCITY ANNOUNCEMENTS:\n" + "\n".join(ann_lines)

        augmented = f"""Context from Syracuse City Open Data:
{context}{ann_context}

---
Question: {user_message}

Answer based on the context above."""

        messages = [{"role": "system", "content": self.system_prompt}]
        messages += self.history[-8:]
        messages.append({"role": "user", "content": augmented})

        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=1024
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"❌ Error: {e}"

        self.history.append({"role": "user",      "content": user_message})
        self.history.append({"role": "assistant",  "content": answer})

        return {
            "answer": answer,
            "sources": [
                {"title": c["title"], "source": c["source"],
                 "category": c["category"], "score": c["score"]}
                for c in chunks if c["score"] > 0.25
            ][:4]
        }

    def reset(self):
        self.history = []
