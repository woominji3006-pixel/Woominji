import streamlit as st
import feedparser
from datetime import datetime
import time

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Climate & Mobility Rights · News",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0d1117;
    color: #e6edf3;
}

/* ── Hero header ── */
.hero {
    padding: 2.5rem 0 1.5rem 0;
    border-bottom: 1px solid #21262d;
    margin-bottom: 2rem;
}
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.6rem;
    line-height: 1.15;
    color: #e6edf3;
    margin: 0 0 0.4rem 0;
}
.hero-title span {
    font-style: italic;
    color: #3fb950;
}
.hero-sub {
    font-size: 0.85rem;
    color: #8b949e;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-weight: 500;
}

/* ── Stats bar ── */
.stats-bar {
    display: flex;
    gap: 2rem;
    padding: 0.9rem 1.2rem;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    margin-bottom: 1.5rem;
    font-size: 0.82rem;
    color: #8b949e;
}
.stat-item strong {
    color: #3fb950;
    font-size: 1.1rem;
    display: block;
    font-weight: 600;
}

/* ── Source badge ── */
.badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.badge-bbc     { background: #1a2b3c; color: #58a6ff; border: 1px solid #1f3a5a; }
.badge-guardian{ background: #1f2d1e; color: #3fb950; border: 1px solid #2d4230; }
.badge-reuters { background: #2d1f1f; color: #f85149; border: 1px solid #4a2020; }

/* ── News card ── */
.news-card {
    padding: 1.1rem 1.3rem;
    background: #161b22;
    border: 1px solid #21262d;
    border-left: 3px solid #21262d;
    border-radius: 10px;
    margin-bottom: 0.75rem;
    transition: border-left-color 0.2s, background 0.2s;
}
.news-card:hover {
    border-left-color: #3fb950;
    background: #1c2128;
}
.news-card-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.05rem;
    color: #e6edf3;
    margin: 0 0 0.45rem 0;
    line-height: 1.4;
}
.news-card-title a {
    color: inherit;
    text-decoration: none;
}
.news-card-title a:hover { color: #3fb950; }
.news-card-meta {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.75rem;
    color: #8b949e;
}

/* ── Keyword tag ── */
.kw-match {
    display: inline-block;
    padding: 1px 7px;
    border-radius: 4px;
    font-size: 0.68rem;
    font-weight: 600;
    background: #0d2818;
    color: #3fb950;
    border: 1px solid #1a4a2e;
    margin-left: 0.3rem;
}

/* ── Streamlit widget overrides ── */
div[data-testid="stTextInput"] input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-family: 'DM Sans', sans-serif !important;
}
div[data-testid="stButton"] button {
    background: #238636 !important;
    color: #fff !important;
    border: 1px solid #2ea043 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 0.4rem 1.2rem !important;
    transition: background 0.2s !important;
}
div[data-testid="stButton"] button:hover {
    background: #2ea043 !important;
}
div[data-testid="stMultiSelect"] > div {
    background: #161b22 !important;
    border-color: #30363d !important;
}
.divider {
    border: none;
    border-top: 1px solid #21262d;
    margin: 1.5rem 0;
}
.no-results {
    text-align: center;
    padding: 3rem 1rem;
    color: #8b949e;
    font-size: 0.9rem;
}
.no-results .icon { font-size: 2.5rem; display: block; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
RSS_SOURCES = {
    "BBC": {
        "url": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "badge_class": "badge-bbc",
        "label": "BBC",
    },
    "The Guardian": {
        "url": "https://www.theguardian.com/environment/climate-crisis/rss",
        "badge_class": "badge-guardian",
        "label": "Guardian",
    },
    "Reuters": {
        "url": "https://feeds.reuters.com/reuters/environmentNews",
        "badge_class": "badge-reuters",
        "label": "Reuters",
    },
}

DEFAULT_KEYWORDS = [
    "climate change", "climate refugees", "mobility rights",
    "climate displacement", "global solidarity", "justice",
    "climate crisis", "emissions", "renewable", "flood", "drought",
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_date(entry) -> str:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6]).strftime("%b %d, %Y")
            except Exception:
                pass
    return "—"


def fetch_feed(source_name: str, source_info: dict) -> list[dict]:
    try:
        feed = feedparser.parse(source_info["url"])
        items = []
        for entry in feed.entries[:30]:
            items.append({
                "title": entry.get("title", "(no title)"),
                "link": entry.get("link", "#"),
                "date": parse_date(entry),
                "source": source_name,
                "badge_class": source_info["badge_class"],
                "label": source_info["label"],
                "summary": entry.get("summary", ""),
            })
        return items
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_all_feeds() -> list[dict]:
    all_items = []
    for name, info in RSS_SOURCES.items():
        all_items.extend(fetch_feed(name, info))
    # Sort by source order preserved; no reliable cross-feed date sort
    return all_items


def highlight_keyword(title: str, keyword: str) -> str:
    """Return matched keyword for badge display."""
    kw_lower = keyword.lower()
    if kw_lower in title.lower():
        return keyword
    return ""


def matches_search(item: dict, query: str, active_keywords: list[str]) -> tuple[bool, list[str]]:
    text = (item["title"] + " " + item["summary"]).lower()
    matched_kws = []

    # Keyword filter
    if active_keywords:
        for kw in active_keywords:
            if kw.lower() in text:
                matched_kws.append(kw)
        if not matched_kws:
            return False, []

    # Free-text search filter
    if query.strip():
        if query.strip().lower() not in text:
            return False, matched_kws

    return True, matched_kws

# ── Session state ─────────────────────────────────────────────────────────────
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-title">🌍 Climate &amp; <span>Mobility Rights</span></div>
    <div class="hero-sub">Live headlines · BBC · The Guardian · Reuters</div>
</div>
""", unsafe_allow_html=True)

# ── Controls row ──────────────────────────────────────────────────────────────
col_search, col_kw, col_btn = st.columns([3, 4, 1], gap="medium")

with col_search:
    search_query = st.text_input(
        "🔍 Search headlines",
        placeholder="e.g. flood, drought, displacement…",
        label_visibility="collapsed",
    )

with col_kw:
    active_keywords = st.multiselect(
        "Filter by keywords",
        options=DEFAULT_KEYWORDS,
        default=[],
        label_visibility="collapsed",
        placeholder="Filter by keyword…",
    )

with col_btn:
    if st.button("↻  Refresh", use_container_width=True):
        fetch_all_feeds.clear()
        st.session_state.last_refresh = time.time()
        st.rerun()

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Fetch data ────────────────────────────────────────────────────────────────
with st.spinner("Fetching latest headlines…"):
    all_articles = fetch_all_feeds()

# ── Filter ────────────────────────────────────────────────────────────────────
filtered = []
for item in all_articles:
    ok, matched = matches_search(item, search_query, active_keywords)
    if ok:
        filtered.append((item, matched))

# ── Stats bar ─────────────────────────────────────────────────────────────────
last_refresh_str = datetime.fromtimestamp(st.session_state.last_refresh).strftime("%H:%M:%S")
source_counts = {s: sum(1 for a, _ in filtered if a["source"] == s) for s in RSS_SOURCES}

st.markdown(f"""
<div class="stats-bar">
    <div class="stat-item"><strong>{len(filtered)}</strong>Articles shown</div>
    <div class="stat-item"><strong>{source_counts.get('BBC', 0)}</strong>BBC</div>
    <div class="stat-item"><strong>{source_counts.get('The Guardian', 0)}</strong>Guardian</div>
    <div class="stat-item"><strong>{source_counts.get('Reuters', 0)}</strong>Reuters</div>
    <div class="stat-item" style="margin-left:auto"><strong>{last_refresh_str}</strong>Last refresh</div>
</div>
""", unsafe_allow_html=True)

# ── Article list ──────────────────────────────────────────────────────────────
if not filtered:
    st.markdown("""
    <div class="no-results">
        <span class="icon">🔎</span>
        No headlines matched your filters.<br>Try different keywords or clear the search.
    </div>
    """, unsafe_allow_html=True)
else:
    for item, matched_kws in filtered:
        kw_badges = "".join(f'<span class="kw-match">{kw}</span>' for kw in matched_kws)
        st.markdown(f"""
        <div class="news-card">
            <div class="news-card-title">
                <a href="{item['link']}" target="_blank" rel="noopener">{item['title']}</a>
                {kw_badges}
            </div>
            <div class="news-card-meta">
                <span class="badge {item['badge_class']}">{item['label']}</span>
                <span>📅 {item['date']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown(
    '<p style="text-align:center;color:#484f58;font-size:0.75rem;">'
    'Data sourced from public RSS feeds · refreshes every 5 minutes automatically'
    '</p>',
    unsafe_allow_html=True,
)
