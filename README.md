# 🏙️ Syracuse City Open Data Chatbot
### Research Task 09 — Syracuse Open Data Civic Project

An AI-powered chatbot that helps Syracuse residents and city officials 
explore real city data from the Syracuse Open Data Portal (data.syr.gov).

---

## Project Summary

This project uses Retrieval-Augmented Generation (RAG) to answer questions
about Syracuse city data including housing violations, lead risk, 311 service
requests, parks, vacant properties, and more — powered by real open datasets
from data.syr.gov.

**Two roles:**
- 🏘️ **City Resident** — housing help, lead risk, parks, services, neighborhood info
- 🏛️ **City Official** — data analysis, violation patterns, resource allocation insights

---

## Data Sources (from data.syr.gov)

| Dataset | Description |
|---|---|
| Lead Risk by Address | Lead paint risk assessments by property |
| Housing Code Violations | Code violations across neighborhoods |
| 311 Service Requests | Resident complaints and requests |
| Demolition Orders | Buildings ordered for demolition |
| Vacant Properties | Abandoned/vacant property registry |
| Parks & Recreation | Facilities, programs, locations |
| Licensed Businesses | Business license registry |
| Neighborhood Boundaries | Geographic neighborhood data |

---

## Project Structure

```
syracuse_city_chatbot/
├── data_loader.py    # Step 1 — Download city data from data.syr.gov
├── ingest.py         # Step 2 — Embed & store in ChromaDB
├── chatbot.py        # Step 3 — RAG engine with Groq
├── app.py            # Step 4 — Streamlit UI (resident + official)
├── requirements.txt
└── README.md
```

---

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get free Groq API key
Go to https://console.groq.com → Sign up → Create API key

### 3. Create .env file
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

### 4. Download city data
```bash
python data_loader.py
```

### 5. Build knowledge base
```bash
python ingest.py
```

### 6. Launch
```bash
streamlit run app.py
```

Open http://localhost:8501

---

## Technical Approach

**RAG Pipeline:**
1. City data downloaded via Socrata API from data.syr.gov
2. Text chunked (600 chars) and embedded with sentence-transformers
3. Stored in ChromaDB local vector database
4. User question → embedded → semantic search → top 6 chunks
5. Chunks + question + role prompt → Groq LLaMA 3.3 70B → answer

**LLM Integration:**
- Role-based system prompts (resident vs official)
- Context grounded in real city data
- Source attribution on every answer
- Conversation history maintained per session

---

## Research Task 09 Alignment

- ✅ Uses real Syracuse Open Data (data.syr.gov)
- ✅ Civic value for residents AND city officials
- ✅ LLM-augmented analysis with RAG
- ✅ Functional deliverable (working chatbot)
- ✅ Documented methodology
- ✅ Data quality awareness (API limits, freshness noted)
- ✅ Multiple stakeholder audiences addressed

---

## Limitations

- Data freshness depends on city portal update frequency
- Some datasets have limited records via free API tier
- Lead risk data is property-level, not individual health data
- 311 data may not reflect all service requests

---

## Contact

Built for Syracuse University Research Task 09 — Syracuse Open Data Civic Project
Data source: https://data.syr.gov
