from typing import Any, Dict, List, Optional

# ──────────────────────────────────────────────
# Common Helpers
# ──────────────────────────────────────────────
def _safe_list(
    value: Any,
    sort_key: Optional[str] = None,
    reverse: bool = False
) -> List[Any]:
    """
    Safely converts input into a sortable list.

    - dict → list(dict.values())
    - list → returned as-is (sorted if possible)
    - anything else → []

    Sorting rules:
    - If sort_key is provided, only dicts are sorted by that key.
    - If sort_key is None, only primitive lists are sorted.
    - Mixed-type lists return unsorted to avoid TypeErrors.
    """

    # Convert dict → list
    if isinstance(value, dict):
        value = list(value.values())

    # Must be a list now
    if not isinstance(value, list):
        return []

    # Mixed types? Don’t sort.
    if sort_key is None and not all(isinstance(x, (int, float, str)) for x in value):
        return value

    try:
        if sort_key:
            return sorted(
                value,
                key=lambda x: x.get(sort_key, "") if isinstance(x, dict) else "",
                reverse=reverse
            )
        return sorted(value, reverse=reverse)
    except Exception:
        return value


def _safe_str(value: Any, default: str = "") -> str:
    """Return value if it's a string, otherwise default."""
    return value if isinstance(value, str) else default


def _safe_get(data: Any, key: str, default: Any = None) -> Any:
    """Safely get a key from a dict-like object."""
    return data.get(key, default) if isinstance(data, dict) else default


def _safe_set(value: Any) -> Dict[str, Any]:
    """Ensure the value is a dictionary."""
    return value if isinstance(value, dict) else {}


# ──────────────────────────────────────────────
# Special NORMALIZERS for scraper
# ──────────────────────────────────────────────

def normalize_raw_data(raw_data: Any) -> Any:
    if isinstance(raw_data, list):
        return [normalize_raw_data(item) for item in raw_data]

    if not isinstance(raw_data, dict):
        return {
            "model_name": "",
            "summary": "",
            "content": [],
            "metadata": [],
        }

    return {
        "model_name": _safe_str(raw_data.get("model_name")),
        "summary": _safe_str(raw_data.get("summary")),
        "content": raw_data.get("content") if isinstance(raw_data.get("content"), list) else [],
        "metadata": raw_data.get("metadata") if isinstance(raw_data.get("metadata"), list) else [],
    }

