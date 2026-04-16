"""
Syracuse City Open Data Loader
Downloads real datasets from data.syr.gov and converts them to text chunks.
Covers: Housing, Lead Risk, Infrastructure, Demographics, Recreation, City Services
"""

import requests
import json
import os
import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_FILE = "city_data.json"

# ── Real Syracuse Open Data API endpoints (Socrata) ───────────────────────────
DATASETS = {
    "lead_risk": {
        "name": "Lead Risk by Address",
        "url": "https://data.syr.gov/resource/gwhf-8a4q.json",
        "description": "Lead paint risk assessments for properties in Syracuse",
        "category": "Housing & Health",
        "limit": 1000
    },
    "housing_violations": {
        "name": "Housing Code Violations",
        "url": "https://data.syr.gov/resource/uvmq-4hy4.json",
        "description": "Housing code violations reported across Syracuse neighborhoods",
        "category": "Housing",
        "limit": 1000
    },
    "demolitions": {
        "name": "Demolition Orders",
        "url": "https://data.syr.gov/resource/7bhn-5phv.json",
        "description": "Buildings ordered for demolition in Syracuse",
        "category": "Infrastructure",
        "limit": 500
    },
    "city_services": {
        "name": "311 Service Requests",
        "url": "https://data.syr.gov/resource/azyx-6zap.json",
        "description": "Resident service requests and complaints submitted to 311",
        "category": "City Services",
        "limit": 1000
    },
    "recreation": {
        "name": "Parks and Recreation Facilities",
        "url": "https://data.syr.gov/resource/4xbr-2czr.json",
        "description": "Parks, playgrounds, and recreation centers in Syracuse",
        "category": "Recreation",
        "limit": 500
    },
    "neighborhoods": {
        "name": "Neighborhood Boundaries",
        "url": "https://data.syr.gov/resource/mfag-atfq.json",
        "description": "Syracuse neighborhood definitions and boundaries",
        "category": "Demographics",
        "limit": 200
    },
    "vacant_properties": {
        "name": "Vacant Properties",
        "url": "https://data.syr.gov/resource/qcbf-3ibu.json",
        "description": "Vacant and abandoned properties across Syracuse",
        "category": "Housing",
        "limit": 1000
    },
    "businesses": {
        "name": "Licensed Businesses",
        "url": "https://data.syr.gov/resource/4d5x-9kty.json",
        "description": "Businesses licensed to operate in Syracuse",
        "category": "Economic Development",
        "limit": 1000
    }
}

# Also scrape key city web pages for context
WEB_PAGES = [
    {"url": "https://data.syr.gov/", "title": "Syracuse Open Data Portal"},
    {"url": "https://www.syracuse.ny.gov/", "title": "City of Syracuse Official Website"},
    {"url": "https://www.syracuse.ny.gov/departments/", "title": "City Departments"},
    {"url": "https://www.syracuse.ny.gov/residents/", "title": "Resident Services"},
    {"url": "https://www.syracuse.ny.gov/housing/", "title": "Housing Services"},
    {"url": "https://www.syracuse.ny.gov/departments/parks-recreation/", "title": "Parks and Recreation"},
    {"url": "https://www.syracuse.ny.gov/departments/code-enforcement/", "title": "Code Enforcement"},
]


def fetch_dataset(key: str, config: dict) -> list[dict]:
    """Download a dataset from data.syr.gov Socrata API."""
    try:
        params = {
            "$limit": config["limit"],
            "$order": ":id",
        }
        resp = requests.get(config["url"], params=params, timeout=30)
        resp.raise_for_status()
        records = resp.json()
        logger.info(f"  ✅ {config['name']}: {len(records)} records")
        return records
    except Exception as e:
        logger.warning(f"  ⚠️ {config['name']}: {e}")
        return []


def records_to_text(key: str, config: dict, records: list[dict]) -> list[dict]:
    """Convert raw API records into readable text documents."""
    if not records:
        return []

    df = pd.DataFrame(records)
    documents = []

    # ── Summary document ──────────────────────────────────────────────────────
    summary_lines = [
        f"Dataset: {config['name']}",
        f"Category: {config['category']}",
        f"Description: {config['description']}",
        f"Total records: {len(records)}",
        f"Data downloaded: {datetime.now().strftime('%Y-%m-%d')}",
        f"Source: {config['url']}",
        "",
        "Available fields: " + ", ".join(df.columns.tolist()[:20]),
    ]

    # Add value counts for key categorical columns
    for col in df.columns[:5]:
        try:
            vc = df[col].value_counts().head(10)
            if len(vc) > 1:
                summary_lines.append(f"\nTop values in '{col}':")
                for val, cnt in vc.items():
                    summary_lines.append(f"  - {val}: {cnt} records")
        except Exception:
            pass

    documents.append({
        "title": f"{config['name']} — Overview",
        "content": "\n".join(summary_lines),
        "category": config["category"],
        "source": config["url"],
        "doc_type": "summary"
    })

    # ── Individual record documents (batched) ─────────────────────────────────
    BATCH = 20
    for i in range(0, min(len(records), 200), BATCH):
        batch = records[i:i+BATCH]
        lines = [f"{config['name']} — Records {i+1} to {i+len(batch)}"]
        for rec in batch:
            line_parts = []
            for k, v in rec.items():
                if v and str(v).strip() and k not in ["the_geom", "geometry", ":@computed_region"]:
                    line_parts.append(f"{k.replace('_', ' ').title()}: {v}")
            if line_parts:
                lines.append("• " + " | ".join(line_parts[:8]))

        documents.append({
            "title": f"{config['name']} — Records batch {i//BATCH + 1}",
            "content": "\n".join(lines),
            "category": config["category"],
            "source": config["url"],
            "doc_type": "records"
        })

    return documents


def scrape_web_page(page: dict) -> dict | None:
    """Scrape a city web page for additional context."""
    try:
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0 (compatible; SyracuseCityBot/1.0)"}
        resp = requests.get(page["url"], headers=headers, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "iframe"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 25]
        content = "\n".join(lines[:200])

        if len(content) < 100:
            return None

        return {
            "title": page["title"],
            "content": content,
            "category": "City Information",
            "source": page["url"],
            "doc_type": "webpage"
        }
    except Exception as e:
        logger.warning(f"  ⚠️ Web page {page['url']}: {e}")
        return None


def load_all() -> list[dict]:
    """Download all datasets and web pages, return unified document list."""
    all_documents = []

    # 1. Open Data datasets
    logger.info("\n📊 Downloading Syracuse Open Data datasets...")
    for key, config in DATASETS.items():
        logger.info(f"Fetching: {config['name']}")
        records = fetch_dataset(key, config)
        docs = records_to_text(key, config, records)
        all_documents.extend(docs)
        logger.info(f"  → {len(docs)} documents created")

    # 2. City web pages
    logger.info("\n🌐 Scraping city web pages...")
    for page in WEB_PAGES:
        logger.info(f"Scraping: {page['url']}")
        doc = scrape_web_page(page)
        if doc:
            all_documents.append(doc)
            logger.info(f"  → Added: {page['title']}")

    # 3. Add static knowledge base
    all_documents.extend(get_static_knowledge())

    return all_documents


def get_static_knowledge() -> list[dict]:
    """Hardcoded key facts about Syracuse city services."""
    return [
        {
            "title": "Syracuse City Key Contacts",
            "content": """Syracuse City Government Key Contacts and Services:

311 Service: Call 311 or visit 311.syracuse.ny.gov for non-emergency city services
Emergency: Call 911 for emergencies
City Hall: 233 E Washington St, Syracuse, NY 13202
Phone: (315) 448-8000

Key Departments:
- Department of Neighborhood & Business Development: Housing assistance, code enforcement
- Parks & Recreation: (315) 473-4330 — parks, programs, facilities
- Department of Public Works: Roads, water, sanitation
- Police Department: (315) 442-5111
- Fire Department: (315) 473-5510
- Office of Code Enforcement: Housing code violations, inspections
- Syracuse Housing Authority: Public housing, Section 8

Lead Paint Resources:
- Onondaga County Health Department Lead Program: (315) 435-3271
- Free lead testing for children under 6
- Lead hazard reduction grants available for property owners

Housing Assistance:
- Home HeadQuarters: (315) 474-1939 — homebuyer assistance, rehabilitation loans
- Syracuse Housing Authority: Public housing applications
- Emergency rental assistance: Contact 211 (dial 2-1-1)

Neighborhood Organizations:
- Syracuse Neighborhood Initiative
- Southside Community Coalition
- Near Westside Initiative
- Syracuse United Neighbors""",
            "category": "City Services",
            "source": "https://www.syracuse.ny.gov",
            "doc_type": "static"
        },
        {
            "title": "Syracuse Neighborhoods Guide",
            "content": """Syracuse Neighborhoods Overview:

North Side: Residential area north of downtown, diverse community
South Side: Large residential neighborhood, community organizations active
West Side: Near Westside Initiative area, revitalization ongoing
East Side: Mix of residential and commercial
Downtown: City center, government, entertainment, SU Hill nearby
Strathmore: Northwest residential neighborhood
Eastwood: Northeast residential, shopping district
Tipp Hill: Irish heritage neighborhood, west side
University Hill: Adjacent to Syracuse University
Lakefront: Near Onondaga Lake, industrial/redevelopment area
Brighton: Southeast residential neighborhood
Valley: South of downtown, residential

Key Community Resources by Area:
- Food pantries: Contact 211 for nearest location
- Community centers: Parks & Recreation department
- Libraries: Onondaga County Public Library system (ocpl.org)
- Schools: Syracuse City School District (scsd.us)""",
            "category": "Demographics",
            "source": "https://www.syracuse.ny.gov",
            "doc_type": "static"
        },
        {
            "title": "Housing Code and Lead Risk in Syracuse",
            "content": """Housing Code Enforcement in Syracuse:

To report a housing code violation:
- Call 311 or visit 311.syracuse.ny.gov
- Department of Code Enforcement handles complaints
- Violations include: unsafe structures, no heat, pest infestations, roof damage

Lead Paint Risk:
- Homes built before 1978 may contain lead paint
- Syracuse has one of the highest childhood lead poisoning rates in NY
- Free blood lead testing for children under 6 at county health department
- Property owners can apply for lead hazard reduction grants
- Lead Safe Syracuse program provides assistance

Vacant Properties:
- Report vacant/abandoned properties through 311
- Land Bank of Central New York acquires and rehabilitates vacant properties
- Contact Land Bank: (315) 422-8290

Rental Housing:
- All rental properties must be registered with the city
- Landlords must maintain properties to code
- Tenants can report violations without fear of retaliation
- Legal Aid Society provides free tenant legal assistance: (315) 475-3127""",
            "category": "Housing & Health",
            "source": "https://www.syracuse.ny.gov/housing",
            "doc_type": "static"
        },
        {
            "title": "Syracuse Parks and Recreation Programs",
            "content": """Syracuse Parks and Recreation:

Contact: (315) 473-4330
Website: syracuse.ny.gov/departments/parks-recreation

Parks: Syracuse has 70+ parks and green spaces
- Burnet Park: Zoo, golf course, tennis
- Thornden Park: Pool, tennis, amphitheater
- Kirk Park: South side community park
- Onondaga Lake Park: Trails, marina, museum (county-operated)

Recreation Centers:
- Southwest Community Center
- Northwest Community Center  
- Fowler Recreation Center
- Bellevue Heights Community Center

Programs offered:
- Youth sports leagues (basketball, soccer, baseball)
- Summer camps and after-school programs
- Senior fitness classes
- Swimming lessons
- Seasonal events and festivals

Registration: Visit parks department or call for program registration
Free programs: Many programs are free or low-cost for Syracuse residents""",
            "category": "Recreation",
            "source": "https://www.syracuse.ny.gov/departments/parks-recreation",
            "doc_type": "static"
        }
    ]


if __name__ == "__main__":
    logger.info("🏙️ Syracuse City Open Data Loader")
    logger.info("=" * 50)

    documents = load_all()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

    logger.info(f"\n✅ Done! {len(documents)} documents saved to {OUTPUT_FILE}")
    categories = {}
    for doc in documents:
        cat = doc.get("category", "Other")
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items()):
        logger.info(f"  {cat}: {count} documents")
