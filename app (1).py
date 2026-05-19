import streamlit as st
import feedparser
from datetime import datetime
import time

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Climate & Mobility Rights · News",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0d1117 !important;
    color: #e6edf3;
}
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.4rem;
    line-height: 1.2;
    color: #e6edf3;
    margin: 1.5rem 0 0.3rem 0;
}
.hero-title em { color: #3fb950; font-style: italic; }
.hero-sub {
    font-size: 0.8rem;
    color: #8b949e;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}
.stats-bar {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
    padding: 0.8rem 1.2rem;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    margin-bottom: 1.2rem;
    font-size: 0.8rem;
    color: #8b949e;
}
.stat-item strong { color: #3fb950; font-size: 1.1rem; display: block; }
.nc {
    padding: 1rem 1.2rem;
    background: #161b22;
    border: 1px solid #21262d;
    border-left: 3px solid #30363d;
    border-radius: 10px;
    margin-bottom: 0.6rem;
}
.nc:hover { border-left-color: #3fb950; background: #1c2128; }
.nc-title { font-family: 'DM Serif Display', serif; font-size: 1.05rem; line-height: 1.4; margin: 0 0 0.4rem; }
.nc-title a { color: #e6edf3; text-decoration: none; }
.nc-title a:hover { color: #3fb950; }
.nc-meta { font-size: 0.74rem; color: #8b949e; margin: 0; }
.bbc     { display:inline-block; padding:1px 8px; border-radius:20px; font-size:0.68rem; font-weight:700;
           text-transform:uppercase; background:#1a2b3c; color:#58a6ff; border:1px solid #1f3a5a; margin-right:6px; }
.guardian{ display:inline-block; padding:1px 8px; border-radius:20px; font-size:0.68rem; font-weight:700;
           text-transform:uppercase; background:#1f2d1e; color:#3fb950; border:1px solid #2d4230; margin-right:6px; }
.reuters { display:inline-block; padding:1px 8px; border-radius:20px; font-size:0.68rem; font-weight:700;
           text-transform:uppercase; background:#2d1f1f; color:#f85149; border:1px solid #4a2020; margin-right:6px; }
.kwtag   { display:inline-block; padding:1px 6px; border-radius:4px; font-size:0.66rem; font-weight:600;
           background:#0d2818; color:#3fb950; border:1px solid #1a4a2e; margin-left:4px; }
.no-res  { text-align:center; padding:3rem 1rem; color:#8b949e; font-size:0.9rem; }
div[data-testid="stTextInput"] input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
}
div[data-testid="stButton"] button {
    background: #238636 !important;
    color: #fff !important;
    border: 1px solid #2ea043 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
div[data-testid="stButton"] button:hover { background: #2ea043 !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
RSS_SOURCES = {
    "BBC": {
        "url": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "cls": "bbc", "label": "BBC",
    },
    "The Guardian": {
        "url": "https://www.theguardian.com/environment/climate-crisis/rss",
        "cls": "guardian", "label": "Guardian",
    },
    "Reuters": {
        "url": "https://feeds.reuters.com/reuters/environmentNews",
        "cls": "reuters", "label": "Reuters",
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

def fetch_feed(source_name: str, info: dict) -> list:
    try:
        feed = feedparser.parse(info["url"])
        items = []
        for entry in feed.entries[:30]:
            items.append({
                "title":   entry.get("title", "(no title)"),
                "link":    entry.get("link", "#"),
                "date":    parse_date(entry),
                "source":  source_name,
                "cls":     info["cls"],
                "label":   info["label"],
                "summary": entry.get("summary", ""),
            })
        return items
    except Exception:
        return []

@st.cache_data(ttl=300, show_spinner=False)
def fetch_all_feeds() -> list:
    all_items = []
    for name, info in RSS_SOURCES.items():
        all_items.extend(fetch_feed(name, info))
    return all_items

def matches(item: dict, query: str, kws: list) -> tuple:
    text = (item["title"] + " " + item["summary"]).lower()
    matched = []
    if kws:
        for kw in kws:
            if kw.lower() in text:
                matched.append(kw)
        if not matched:
            return False, []
    if query.strip() and query.strip().lower() not in text:
        return False, matched
    return True, matched

def render_card(item: dict, matched_kws: list):
    kw_html  = "".join(f'<span class="kwtag">{kw}</span>' for kw in matched_kws)
    badge    = f'<span class="{item["cls"]}">{item["label"]}</span>'
    # Flat HTML — p tags only, no nested divs, avoids Streamlit HTML sandbox escape
    html = (
        '<div class="nc">'
        f'<p class="nc-title"><a href="{item["link"]}" target="_blank" rel="noopener">'
        f'{item["title"]}</a>{kw_html}</p>'
        f'<p class="nc-meta">{badge}&#128197; {item["date"]}</p>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    '<p class="hero-title">🌍 Climate &amp; <em>Mobility Rights</em></p>'
    '<p class="hero-sub">Live Headlines &nbsp;·&nbsp; BBC &nbsp;·&nbsp; The Guardian &nbsp;·&nbsp; Reuters</p>',
    unsafe_allow_html=True,
)
st.divider()

# ── Controls ──────────────────────────────────────────────────────────────────
col_s, col_k, col_b = st.columns([3, 4, 1], gap="medium")
with col_s:
    query = st.text_input("search", placeholder="e.g. flood, drought, displacement…",
                          label_visibility="collapsed")
with col_k:
    active_kws = st.multiselect("keywords", options=DEFAULT_KEYWORDS, default=[],
                                label_visibility="collapsed", placeholder="Filter by keyword…")
with col_b:
    if st.button("↻  Refresh", use_container_width=True):
        fetch_all_feeds.clear()
        st.session_state.last_refresh = time.time()
        st.rerun()

st.divider()

# ── Fetch & filter ────────────────────────────────────────────────────────────
with st.spinner("Fetching latest headlines…"):
    all_articles = fetch_all_feeds()

filtered = []
for item in all_articles:
    ok, matched = matches(item, query, active_kws)
    if ok:
        filtered.append((item, matched))

# ── Stats bar ─────────────────────────────────────────────────────────────────
ts = datetime.fromtimestamp(st.session_state.last_refresh).strftime("%H:%M:%S")
sc = {s: sum(1 for a, _ in filtered if a["source"] == s) for s in RSS_SOURCES}
st.markdown(
    f'<div class="stats-bar">'
    f'<div class="stat-item"><strong>{len(filtered)}</strong>Articles shown</div>'
    f'<div class="stat-item"><strong>{sc.get("BBC",0)}</strong>BBC</div>'
    f'<div class="stat-item"><strong>{sc.get("The Guardian",0)}</strong>Guardian</div>'
    f'<div class="stat-item"><strong>{sc.get("Reuters",0)}</strong>Reuters</div>'
    f'<div class="stat-item" style="margin-left:auto"><strong>{ts}</strong>Last refresh</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Article list ──────────────────────────────────────────────────────────────
if not filtered:
    st.markdown(
        '<div class="no-res">🔎<br>No headlines matched. Try different keywords or clear the search.</div>',
        unsafe_allow_html=True,
    )
else:
    for item, matched_kws in filtered:
        render_card(item, matched_kws)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    '<p style="text-align:center;color:#484f58;font-size:0.75rem;">'
    'Public RSS feeds only · auto-refreshes every 5 min</p>',
    unsafe_allow_html=True,
)
