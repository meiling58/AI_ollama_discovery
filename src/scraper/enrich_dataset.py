import json
from pathlib import Path

# -----------------------------
# Paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"


# -----------------------------
# Load merged dataset
# -----------------------------
def load_merged():
    with open(DATA_DIR / "ollama_library_merged.json", "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# Safe helpers
# -----------------------------
def safe_str(val):
    return val if isinstance(val, str) else ""


def safe_dict(val):
    return val if isinstance(val, dict) else {}


def parse_number(text):
    if not text:
        return None

    text = str(text).upper().strip()

    try:
        if "M" in text:
            return float(text.replace("M", "")) * 1_000_000
        if "K" in text:
            return float(text.replace("K", "")) * 1_000
        return float(text)
    except:
        return None


def parse_context(ctx):
    if not ctx:
        return None
    try:
        ctx = str(ctx).upper().replace("K", "")
        return int(float(ctx) * 1000)
    except:
        return None


def parse_size(size):
    if not size:
        return None

    size = str(size).upper().strip()

    try:
        if "TB" in size:
            return float(size.replace("TB", "")) * 1024 * 1024
        if "GB" in size:
            return float(size.replace("GB", "")) * 1024
        if "MB" in size:
            return float(size.replace("MB", ""))
    except:
        return None

    return None


# -----------------------------
# Capability enrichment
# -----------------------------
def enrich_capabilities(model):
    caps = set(model.get("capabilities", []))

    versions = model.get("versions") or []
    summary = safe_str(model.get("summary")).lower()
    name = safe_str(model.get("model_name")).lower()

    for v in versions:
        input_type = safe_str(v.get("input")).lower()

        if "image" in input_type:
            caps.add("vision")
        if "text" in input_type:
            caps.add("text")

    if "embed" in name:
        caps.add("embedding")

    if "tool" in summary or "function calling" in summary:
        caps.add("tools")

    if "moe" in summary or "mixture-of-experts" in summary or "reasoning" in summary:
        caps.add("thinking")

    # cloud hint (raw signal)
    latest = safe_dict(model.get("latest"))
    size_str = safe_str(latest.get("size"))

    latest_size = parse_size(size_str)
    if latest_size and latest_size > 50000:
        caps.add("cloud")

    return sorted(caps)


# -----------------------------
# Model classification
# -----------------------------
def classify_model(model):
    latest = safe_dict(model.get("latest"))
    size = parse_size(latest.get("size"))

    if not size:
        return "unknown"

    if size < 2000:
        return "small"
    elif size < 10000:
        return "medium"
    elif size < 50000:
        return "large"
    else:
        return "xl"


# -----------------------------
# Cloud / deployment logic
# -----------------------------
def has_small_quantized_version(versions):
    for v in versions:
        name = safe_str(v.get("name")).lower()
        size = parse_size(v.get("size"))

        if size and size < 10000 and "q" in name:
            return True

    return False


def compute_deployment(model):
    versions = model.get("versions") or []

    latest = safe_dict(model.get("latest"))
    latest_size = parse_size(latest.get("size"))

    has_small_quant = has_small_quantized_version(versions)

    if has_small_quant:
        return "local"

    if latest_size and latest_size > 50000:
        return "cloud"

    return "hybrid"


def pick_best_version(versions):
    if not versions:
        return None

    for v in versions:
        if "q4" in safe_str(v.get("name")).lower():
            return v

    return versions[0]


# -----------------------------
# Enrich single model
# -----------------------------
def enrich_model(model):
    model = model or {}

    versions = model.get("versions") or []

    caps = enrich_capabilities(model)

    sizes = [parse_size(v.get("size")) for v in versions]
    sizes = [s for s in sizes if s is not None]

    contexts = [parse_context(v.get("context")) for v in versions]
    contexts = [c for c in contexts if c is not None]

    metadata = safe_dict(model.get("metadata"))
    latest = safe_dict(model.get("latest"))

    pulls = parse_number(metadata.get("pulls"))
    latest_size = parse_size(latest.get("size"))

    return {
        **model,
        "capabilities": caps,
        "best_version": pick_best_version(versions),
        "derived": {
            # structure
            "version_count": len(versions),
            "has_quantized": any("q" in safe_str(v.get("name")).lower() for v in versions),

            # size
            "max_size_mb": max(sizes) if sizes else None,
            "min_size_mb": min(sizes) if sizes else None,
            "latest_size_mb": latest_size,

            # context
            "max_context": max(contexts) if contexts else None,

            # usage
            "pulls": pulls,

            # classification
            "model_class": classify_model(model),

            # capabilities flags
            "supports_vision": "vision" in caps,
            "supports_tools": "tools" in caps,
            "supports_embeddings": "embedding" in caps,
            "supports_thinking": "thinking" in caps,

            # deployment strategy (NEW)
            "deployment": compute_deployment(model),
        }
    }


# -----------------------------
# Main pipeline
# -----------------------------
def enrich_all():
    data = load_merged()

    enriched = [enrich_model(m) for m in data]

    output = DATA_DIR / "ollama_library_enriched.json"

    with open(output, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2)

    print(f"[ENRICHED] Saved to {output}")


if __name__ == "__main__":
    enrich_all()