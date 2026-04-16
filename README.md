# 🏙️ Syracuse City Chatbot
### OPT Project — Syracuse Open Data Civic AI

> An AI-powered chatbot for Syracuse residents and city officials, built on real open data from [data.syr.gov](https://data.syr.gov) using RAG + Groq LLaMA 3.3.

---

## Project Progress Log

| # | Task | Status |
|---|------|--------|
| 01 | Project scoping & dataset identification | ✅ Done |
| 02 | Syracuse Open Data API integration (`data_loader.py`) | ✅ Done |
| 03 | Text chunking & embedding pipeline | ✅ Done |
| 04 | ChromaDB vector store setup (`ingest.py`) | ✅ Done |
| 05 | RAG chatbot engine with Groq (`chatbot.py`) | ✅ Done |
| 06 | Streamlit UI — Resident & Official modes (`app.py`) | ✅ Done |
| 07 | Role-based prompting & source attribution | ✅ Done |
| 08 | City Official announcement system | ✅ Done |
| 09 | Bug fixes & deployment polish | ✅ Done |

---

## What It Does

Two user roles, one chatbot backed by real Syracuse city data:

- 🏘️ **City Resident** — Ask about housing violations, lead risk, parks, 311 services, vacant properties, neighborhood resources
- 🏛️ **City Official** — Analyze violation patterns, lead risk by neighborhood, 311 trends, demolition data, post city announcements

---

## Data Sources

All data pulled live from the [Syracuse Open Data Portal](https://data.syr.gov) via Socrata API:

| Dataset | Description |
|---------|-------------|
| Lead Risk by Address | Lead paint risk assessments by property |
| Housing Code Violations | Code violations across neighborhoods |
| 311 Service Requests | Resident complaints and service requests |
| Demolition Orders | Buildings ordered for demolition |
| Vacant Properties | Abandoned/vacant property registry |
| Parks & Recreation | Facilities, programs, and locations |
| Licensed Businesses | Business license registry |
| Neighborhood Boundaries | Geographic neighborhood data |

---

## Tech Stack

| Layer | Tool |
|-------|------|
| LLM | Groq — LLaMA 3.3 70B |
| Embeddings | `sentence-transformers` |
| Vector DB | ChromaDB (local) |
| UI | Streamlit |
| Data API | Socrata / data.syr.gov |

---

## Project Structure

```
City_Chatbot/
├── data_loader.py    # Step 1 — Download city datasets from data.syr.gov
├── ingest.py         # Step 2 — Embed & store in ChromaDB
├── chatbot.py        # Step 3 — RAG engine (Groq + ChromaDB)
├── app.py            # Step 4 — Streamlit UI (resident + official modes)
├── requirements.txt
└── .env              # GROQ_API_KEY (not committed)
```

---

## Setup & Run

### 1. Clone & install
```bash
git clone https://github.com/shubhp19/City_Chatbot.git
cd City_Chatbot
pip install -r requirements.txt
```

### 2. Get a free Groq API key
Sign up at [console.groq.com](https://console.groq.com) → Create API key

### 3. Create `.env`
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

### 4. Download city data
```bash
python data_loader.py
```

### 5. Build the knowledge base
```bash
python ingest.py
```

### 6. Launch
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501)

---

## RAG Pipeline

```
User Question
     ↓
Embed with sentence-transformers
     ↓
Semantic search → Top 6 chunks from ChromaDB
     ↓
Role-based system prompt + context + question
     ↓
Groq LLaMA 3.3 70B
     ↓
Answer + source attribution
```

---

## Research Alignment

- ✅ Real Syracuse Open Data (data.syr.gov)
- ✅ Civic value for residents AND city officials
- ✅ LLM + RAG — grounded, not hallucinated
- ✅ Functional deliverable (working chatbot)
- ✅ Multiple stakeholder audiences
- ✅ Source attribution on every answer

---

Built for Syracuse University OPT Project — Syracuse Open Data Civic AI
