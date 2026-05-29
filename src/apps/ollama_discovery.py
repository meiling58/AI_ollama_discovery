import streamlit as st
import json
from pathlib import Path
from src.utils import capabilities

# ============================
# CONFIG
# ============================
st.set_page_config(
    page_title="Ollama Discovery",
    page_icon="🧐",
    layout="wide"
)

# ============================
# LOAD DATA
# ============================
DATA_DIR = Path("data")
FILE = DATA_DIR / "ollama_library_enriched.json"

with open(FILE, "r", encoding="utf-8") as f:
    RAW_MODELS = json.load(f)

capabilities_list = capabilities.get_capabilities()

# ============================
# HELPERS
# ============================
def parse_size(size_str):
    if not size_str:
        return None

    size_str = size_str.upper().strip()

    try:
        if "GB" in size_str:
            return float(size_str.replace("GB", "").strip()) * 1024
        if "MB" in size_str:
            return float(size_str.replace("MB", "").strip())
    except:
        return None

    return None


def mb_to_gb(mb):
    return mb / 1024 if mb is not None else None


def size_band(gb):
    if gb is None:
        return "Unknown"
    if gb <= 2:
        return "Tiny (≤2GB)"
    elif gb <= 6:
        return "Small (2–6GB)"
    elif gb <= 12:
        return "Medium (6–12GB)"
    elif gb <= 24:
        return "Large (12–24GB)"
    else:
        return "XL (24GB+)"


def enrich(models):
    for m in models:
        latest = m.get("latest", {})
        m["size_mb"] = parse_size(latest.get("size"))
        m["size_gb"] = mb_to_gb(m["size_mb"])
        m["size_band"] = size_band(m["size_gb"])
    return models

# ============================
# DATA PREP
# ============================
MODELS = enrich(RAW_MODELS)

# ============================
# HEADER
# ============================
st.markdown(
    """
    <h1 style='margin-bottom:0'>🧐 Ollama Models Discovery</h1>
    <p style='color:gray;margin-top:5px'>Discover, filter, and explore Ollama models with smart, real-time insights.</p>
    """,
    unsafe_allow_html=True
)

st.divider()

# ============================
# SIDEBAR (UNIFIED FILTER STATE)
# ============================
with st.sidebar:
    st.header("🎛️ Filters")

    filter_state = {}

    filter_state["search"] = st.text_input("🔍 Search models")

    filter_state["sort_by"] = st.selectbox(
        "Sort by",
        [
            "Relevance",
            "Name A–Z",
            "Size (small → large)",
            "Size (large → small)"
        ]
    )

    filter_state["capabilities"] = st.multiselect(
        "🧠 Capabilities",
        capabilities_list
    )

    filter_state["size_mode"] = st.radio(
        "📦 Size Filter",
        ["Slider", "Bands"],
        horizontal=True
    )

    valid_sizes = [m["size_gb"] for m in MODELS if m.get("size_gb")]
    max_gb = max(valid_sizes) if valid_sizes else 0

    if filter_state["size_mode"] == "Slider":
        filter_state["size"] = {
            "type": "max",
            "value": st.slider("Max Size (GB)", 0.0, float(max_gb), float(max_gb), 0.5)
        }
    else:
        bands = st.multiselect(
            "Size Bands",
            ["Tiny (≤2GB)", "Small (2–6GB)", "Medium (6–12GB)", "Large (12–24GB)", "XL (24GB+)", "Unknown"],
            default=["Tiny (≤2GB)", "Small (2–6GB)", "Medium (6–12GB)", "Large (12–24GB)", "XL (24GB+)"]
        )
        filter_state["size"] = {
            "type": "bands",
            "value": bands
        }

    st.subheader("ℹ️ Capability meanings")
    with st.expander("Click for details"):
        st.caption("tools → agents & automation")
        st.caption("vision → image understanding")
        st.caption("embedding → vector search")
        st.caption("cloud → hosted optimization")
        st.caption("thinking → reasoning strength")
        st.caption("audio → processes audio input")


# ============================
# FILTER LOGIC
# ============================
filtered = MODELS

if filter_state["search"]:
    filtered = [
        m for m in filtered
        if filter_state["search"].lower() in m.get("model_name", "").lower()
    ]

if filter_state["capabilities"]:
    filtered = [
        m for m in filtered
        if any(c in m.get("capabilities", []) for c in filter_state["capabilities"])
    ]

size_filter = filter_state["size"]

if size_filter["type"] == "max":
    max_size = size_filter["value"]
    filtered = [
        m for m in filtered
        if not m.get("size_gb") or m["size_gb"] <= max_size
    ]

elif size_filter["type"] == "bands":
    selected_bands = size_filter["value"]
    filtered = [
        m for m in filtered
        if m.get("size_band") in selected_bands
    ]

# ============================
# SORTING
# ============================
sort_by = filter_state["sort_by"]

if sort_by == "Name A–Z":
    filtered.sort(key=lambda x: x.get("model_name", ""))
elif sort_by == "Size (small → large)":
    filtered.sort(key=lambda x: x.get("size_gb") or 9999)
elif sort_by == "Size (large → small)":
    filtered.sort(key=lambda x: x.get("size_gb") or 0, reverse=True)

# ============================
# METRICS
# ============================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Models", len(filtered))
col2.metric("Total", len(MODELS))
col3.metric("Capabilities", len(filter_state["capabilities"]) if filter_state["capabilities"] else len(capabilities_list))

if size_filter["type"] == "max":
    col4.metric("Max Size", f"{size_filter['value']:.1f} GB")
else:
    col4.metric("Bands", f"{len(size_filter['value'])} selected")

st.divider()

# ============================
# CARD GRID
# ============================
cols_per_row = 3
rows = [filtered[i:i + cols_per_row] for i in range(0, len(filtered), cols_per_row)]

for row in rows:
    cols = st.columns(cols_per_row)

    for idx, model in enumerate(row):
        with cols[idx]:
            with st.container(border=True):
                st.subheader(model.get("model_name", "Unknown"))

                st.caption(model.get("summary", "No summary available"))

                caps = model.get("capabilities", [])
                st.markdown("🧠 " + (", ".join(caps) if caps else "N/A"))

                if model.get("size_gb"):
                    st.metric("Size", f"{model['size_gb']:.2f} GB")
                else:
                    st.metric("Size", "Unknown")

                st.caption(model.get("size_band", ""))

                latest = model.get("latest", {})
                if latest:
                    st.caption(f"📦 {latest.get('latest', '')}")

                with st.expander("Details"):
                    st.write("Content:", model.get("content", []))
                    st.write("Usage:", latest.get("usage_command", ""))

                versions = model.get("versions", [])
                with st.expander("📚 All Versions"):
                    for v in versions:
                        st.write(
                            f"- **{v.get('name')}** | {v.get('size')} | {v.get('usage_command')} | Updated: {v.get('updated_at')}"
                        )

# ============================
# FOOTER
# ============================
st.divider()
st.caption("Built for Ollama models discovery 🚀")
