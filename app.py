"""
Syracuse City Open Data Chatbot
Research Task 09 — Civic AI Project
Streamlit UI with Resident and City Official modes
"""

import streamlit as st
import os
from chatbot import SyracuseCityChatbot

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

st.set_page_config(
    page_title="Syracuse City Assistant",
    page_icon="🏙️",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.city-header { text-align:center; padding:1.2rem 0 0.4rem; }
.city-header h1 { font-family:'DM Serif Display',serif; font-size:2rem; color:var(--color-text-primary); margin:0; }
.city-header p  { color:var(--color-text-secondary); font-size:0.85rem; margin:0.3rem 0 0; }

.pill-resident { background:#0052A5; color:#fff; padding:3px 14px; border-radius:20px; font-size:0.78rem; }
.pill-official { background:#C8102E; color:#fff; padding:3px 14px; border-radius:20px; font-size:0.78rem; }

.ann-card {
    background:var(--color-background-secondary);
    border-left:4px solid #C8102E;
    padding:0.7rem 1rem;
    border-radius:0 8px 8px 0;
    margin-bottom:0.5rem;
}
.ann-cat   { font-size:0.7rem; color:#C8102E; font-weight:600; text-transform:uppercase; }
.ann-title { font-size:0.92rem; font-weight:600; color:var(--color-text-primary); margin:2px 0; }
.ann-body  { font-size:0.83rem; color:var(--color-text-secondary); }
.ann-meta  { font-size:0.7rem; color:var(--color-text-tertiary); margin-top:4px; }

.source-chip {
    display:inline-block; background:var(--color-background-secondary);
    color:var(--color-text-secondary); padding:3px 10px;
    border-radius:20px; font-size:0.72rem; margin:2px;
    text-decoration:none; border:1px solid var(--color-border-tertiary);
}

.stat-box {
    background:var(--color-background-secondary);
    border-radius:10px; padding:1rem;
    text-align:center; border:1px solid var(--color-border-tertiary);
}
.stat-num  { font-size:1.6rem; font-weight:600; color:var(--color-text-primary); }
.stat-label{ font-size:0.78rem; color:var(--color-text-secondary); }
</style>
""", unsafe_allow_html=True)


# ── Login ──────────────────────────────────────────────────────────────────────
def show_login():
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("""
        <div class="city-header">
            <h1>🏙️ Syracuse City Assistant</h1>
            <p>Powered by Syracuse Open Data · data.syr.gov · Built for Research Task 09</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        api_key = os.environ.get("GROQ_API_KEY", "")

        st.markdown("##### 👤 Who are you?")
        col1, col2 = st.columns(2)
        with col1:
            res_btn = st.button("🏘️ City Resident", use_container_width=True, type="primary")
        with col2:
            off_btn = st.button("🏛️ City Official", use_container_width=True)

        if res_btn:
            st.session_state.api_key  = api_key
            st.session_state.role     = "resident"
            st.rerun()
        elif off_btn:
            st.session_state.api_key  = api_key
            st.session_state.role     = "official"
            st.session_state.needs_name = True
            st.rerun()

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div style="background:var(--color-background-secondary);border-radius:10px;padding:1rem;border:1px solid var(--color-border-tertiary)">
            <b>🏘️ Residents can ask about:</b><br>
            🏠 Housing violations & lead risk<br>
            🌳 Parks & recreation programs<br>
            📞 City services & 311 requests<br>
            🗺️ Neighborhood resources<br>
            🏚️ Vacant & abandoned properties
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="background:var(--color-background-secondary);border-radius:10px;padding:1rem;border:1px solid var(--color-border-tertiary)">
            <b>🏛️ City Officials can explore:</b><br>
            📊 Housing violation patterns<br>
            🗺️ Lead risk by neighborhood<br>
            📈 311 request trends<br>
            🏗️ Demolition & vacancy data<br>
            📢 Post city announcements
            </div>
            """, unsafe_allow_html=True)


def show_name_form():
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("### 🏛️ Welcome, City Official!")
        name = st.text_input("Your name", placeholder="Jane Smith")
        dept = st.text_input("Your department", placeholder="Office of Accountability & Performance")
        if st.button("Continue →", type="primary"):
            if name:
                st.session_state.official_name = name
                st.session_state.official_dept = dept
                st.session_state.pop("needs_name", None)
                st.rerun()
            else:
                st.error("Please enter your name.")


# ── Resident Chat ──────────────────────────────────────────────────────────────
def show_resident():
    if "bot" not in st.session_state:
        with st.spinner("Loading Syracuse city data..."):
            st.session_state.bot = SyracuseCityChatbot(
                api_key=st.session_state.api_key, role="resident")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content":
            "Hi! 👋 I'm your Syracuse City Assistant. Ask me about **housing issues, lead paint risk, parks & recreation, city services, or your neighborhood**. I'm here to help!"}]

    chat_col, info_col = st.columns([2, 1])

    with chat_col:
        st.markdown("""
        <div class="city-header" style="text-align:left;padding:0.5rem 0">
            <h1 style="font-size:1.5rem">🏙️ Syracuse City Assistant
            <span class="pill-resident">Resident</span></h1>
        </div>""", unsafe_allow_html=True)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sources"):
                    chips = " ".join(
                        f'<a class="source-chip" href="{s["source"]}" target="_blank">📄 {s["title"][:35]}</a>'
                        for s in msg["sources"] if s.get("source")
                    )
                    st.markdown(f"<div style='margin-top:6px'>{chips}</div>", unsafe_allow_html=True)

        user_input = st.session_state.pop("pending", None) or \
                     st.chat_input("Ask about housing, parks, services, lead risk...")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.chat_message("assistant"):
                with st.spinner("Searching city data..."):
                    result = st.session_state.bot.chat(user_input)
                st.markdown(result["answer"])
                sources = result.get("sources", [])
                if sources:
                    chips = " ".join(
                        f'<a class="source-chip" href="{s["source"]}" target="_blank">📄 {s["title"][:35]}</a>'
                        for s in sources if s.get("source")
                    )
                    st.markdown(f"<div style='margin-top:6px'>{chips}</div>", unsafe_allow_html=True)
            st.session_state.messages.append({
                "role": "assistant", "content": result["answer"], "sources": sources})

    with info_col:
        anns = st.session_state.bot.announcements.get_all()
        if anns:
            st.markdown("#### 📢 City Announcements")
            for ann in reversed(anns[-4:]):
                st.markdown(f"""
                <div class="ann-card">
                    <div class="ann-cat">{ann['category']}</div>
                    <div class="ann-title">{ann['title']}</div>
                    <div class="ann-body">{ann['body']}</div>
                    <div class="ann-meta">— {ann['author']} · {ann['posted_at']}</div>
                </div>""", unsafe_allow_html=True)
            st.divider()

        st.markdown("#### 💡 Common Questions")
        questions = [
            "Is my neighborhood high lead risk?",
            "How do I report a housing violation?",
            "What parks are near me?",
            "How do I apply for housing assistance?",
            "What is the 311 service?",
            "How do I report a vacant property?",
            "What recreation programs exist for kids?",
            "What neighborhoods have most violations?",
        ]
        for i, q in enumerate(questions):
            if st.button(q, use_container_width=True, key=f"r_{i}"):
                st.session_state.pending = q
                st.rerun()

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.messages = [{"role": "assistant",
                    "content": "Chat cleared! How can I help?"}]
                st.session_state.bot.reset()
                st.rerun()
        with col2:
            if st.button("🔄 Switch", use_container_width=True):
                for k in ["role","bot","messages","pending",
                          "official_name","official_dept"]:
                    st.session_state.pop(k, None)
                st.rerun()


# ── Official Dashboard ─────────────────────────────────────────────────────────
def show_official():
    name = st.session_state.get("official_name", "Official")
    dept = st.session_state.get("official_dept", "")

    if "bot" not in st.session_state:
        with st.spinner("Loading Syracuse city data..."):
            st.session_state.bot = SyracuseCityChatbot(
                api_key=st.session_state.api_key, role="official")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content":
            f"Hello, {name}! 👋 I can help you **analyze housing violations, lead risk patterns, 311 trends, vacancy data, and neighborhood demographics**. What would you like to explore?"}]

    chat_col, tools_col = st.columns([2, 1])

    with chat_col:
        st.markdown(f"""
        <div class="city-header" style="text-align:left;padding:0.5rem 0">
            <h1 style="font-size:1.5rem">🏙️ City Data Dashboard
            <span class="pill-official">City Official</span></h1>
            <p>{name} · {dept}</p>
        </div>""", unsafe_allow_html=True)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sources"):
                    chips = " ".join(
                        f'<a class="source-chip" href="{s["source"]}" target="_blank">📊 {s["title"][:35]}</a>'
                        for s in msg["sources"] if s.get("source")
                    )
                    st.markdown(f"<div style='margin-top:6px'>{chips}</div>", unsafe_allow_html=True)

        user_input = st.session_state.pop("pending", None) or \
                     st.chat_input("Analyze housing, violations, lead risk, 311 trends...")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.chat_message("assistant"):
                with st.spinner("Analyzing city data..."):
                    result = st.session_state.bot.chat(user_input)
                st.markdown(result["answer"])
                sources = result.get("sources", [])
                if sources:
                    chips = " ".join(
                        f'<a class="source-chip" href="{s["source"]}" target="_blank">📊 {s["title"][:35]}</a>'
                        for s in sources if s.get("source")
                    )
                    st.markdown(f"<div style='margin-top:6px'>{chips}</div>", unsafe_allow_html=True)
            st.session_state.messages.append({
                "role": "assistant", "content": result["answer"], "sources": sources})

    with tools_col:
        tab1, tab2, tab3 = st.tabs(["📊 Data", "📢 Announce", "💡 Quick"])

        with tab1:
            st.markdown("#### Data Categories")
            categories = ["Housing", "Housing & Health", "Infrastructure",
                          "City Services", "Recreation", "Demographics",
                          "Economic Development", "City Information"]
            for cat in categories:
                st.markdown(f"- **{cat}**")
            st.divider()
            st.markdown("#### Data Sources")
            st.markdown("[data.syr.gov](https://data.syr.gov) — Syracuse Open Data Portal")
            st.markdown("[311.syracuse.ny.gov](https://311.syracuse.ny.gov) — 311 Service")

        with tab2:
            st.markdown("#### Post City Announcement")
            cat   = st.selectbox("Category", ["Housing", "Health", "Safety",
                                               "Parks & Recreation", "Infrastructure", "General"])
            title = st.text_input("Title", placeholder="Water Main Work on Main St")
            body  = st.text_area("Message", height=90,
                                  placeholder="Water service will be interrupted...")
            if st.button("📢 Post", type="primary", use_container_width=True):
                if title and body:
                    ann = st.session_state.bot.announcements.post(
                        author=name, category=cat, title=title, body=body)
                    st.success(f"✅ Posted! (ID #{ann['id']})")
                    st.rerun()
                else:
                    st.error("Fill in all fields.")

            st.divider()
            st.markdown("#### Manage Announcements")
            all_anns = st.session_state.bot.announcements.get_all()
            my_anns  = [a for a in all_anns if a.get("author") == name]
            if not my_anns:
                st.caption("No announcements yet.")
            for ann in reversed(my_anns):
                with st.expander(f"[{ann['category']}] {ann['title']}"):
                    st.write(ann["body"])
                    st.caption(f"Posted: {ann['posted_at']}")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("💾 Keep", key=f"k_{ann['id']}", use_container_width=True):
                            pass
                    with c2:
                        if st.button("🗑️ Delete", key=f"d_{ann['id']}", use_container_width=True):
                            st.session_state.bot.announcements.delete(ann["id"])
                            st.rerun()

        with tab3:
            st.markdown("#### Analysis Questions")
            questions = [
                "Which neighborhoods have most housing violations?",
                "What are the top lead risk areas?",
                "How many vacant properties are there?",
                "What are the most common 311 requests?",
                "Which areas need most code enforcement?",
                "Show demolition order patterns",
                "What businesses are licensed in Syracuse?",
                "What are housing violation trends?",
            ]
            for i, q in enumerate(questions):
                if st.button(q, use_container_width=True, key=f"o_{i}"):
                    st.session_state.pending = q
                    st.rerun()

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.messages = [{"role": "assistant",
                    "content": "Chat cleared! What would you like to analyze?"}]
                st.session_state.bot.reset()
                st.rerun()
        with col2:
            if st.button("🔄 Switch", use_container_width=True):
                for k in ["role","bot","messages","pending",
                          "official_name","official_dept"]:
                    st.session_state.pop(k, None)
                st.rerun()


# ── Router ─────────────────────────────────────────────────────────────────────
if "role" not in st.session_state or "api_key" not in st.session_state:
    show_login()
elif st.session_state.get("needs_name"):
    show_name_form()
elif st.session_state.role == "resident":
    show_resident()
else:
    show_official()
