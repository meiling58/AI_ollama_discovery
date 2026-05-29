import json
import csv
import hashlib
from datetime import datetime
from typing import Any
from pathlib import Path
import yaml

from src.utils.file_paths import DATA_DIR


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _ensure_path(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _hash_data(data: Any) -> str:
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(serialized.encode("utf-8")).hexdigest()


def _load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_txt(path: Path):
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _load_yaml(path: Path):
    if not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None


def _is_dict_dataset(data: Any) -> bool:
    return isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict)


# ──────────────────────────────────────────────
# Change Detection
# ──────────────────────────────────────────────

def detect_changes(new_data, existing_data, record_id="model_name"):
    """
    Works for BOTH:
    - list[dict] (models)
    - list[str] or simple lists (tags)
    """

    # ── SIMPLE LIST DATA (tags, etc.)
    if not _is_dict_dataset(new_data):
        return {
            "has_changes": new_data != existing_data,
            "added_count": 0,
            "removed_count": 0,
            "modified_count": 0,
            "added": [],
            "removed": [],
            "modified": [],
            "checked_at": datetime.now().isoformat(),
        }

    # ── DICT DATASETS (models)
    existing_data = existing_data or []

    existing_map = {
        row.get(record_id): row
        for row in existing_data
        if isinstance(row, dict) and record_id in row
    }

    new_map = {
        row.get(record_id): row
        for row in new_data
        if isinstance(row, dict) and record_id in row
    }

    added = [row for k, row in new_map.items() if k not in existing_map]
    removed = [row for k, row in existing_map.items() if k not in new_map]

    modified = [
        {
            "before": existing_map[k],
            "after": row
        }
        for k, row in new_map.items()
        if k in existing_map and existing_map[k] != row
    ]

    return {
        "has_changes": bool(added or removed or modified),
        "added_count": len(added),
        "removed_count": len(removed),
        "modified_count": len(modified),
        "added": added,
        "removed": removed,
        "modified": modified,
        "checked_at": datetime.now().isoformat(),
    }


def _print_change_report(report: dict, label: str) -> None:
    print(f"\n[{label}] Dataset Change Report — {report['checked_at']}")

    if not report["has_changes"]:
        print("  ✔ No changes detected. File not overwritten.")
        return

    print(f"  + Added   : {report['added_count']}")
    print(f"  - Removed : {report['removed_count']}")
    print(f"  ~ Modified: {report['modified_count']}")


def save_change_log(report: dict, path: Path | None = None) -> None:
    path = path or DATA_DIR / "change_log.json"
    _ensure_path(path)

    history = []
    if path.exists():
        history = json.loads(path.read_text(encoding="utf-8"))

    history.append(report)
    path.write_text(json.dumps(history, indent=4, ensure_ascii=False), encoding="utf-8")


# ──────────────────────────────────────────────
# SAVE FUNCTIONS
# ──────────────────────────────────────────────

def save_json(data: list[dict], filename="dataset", path: Path | None = None, log_changes=True):
    path = path or (DATA_DIR / f"{filename}.json")
    _ensure_path(path)

    existing = _load_json(path)

    if existing is not None:
        if _hash_data(existing) == _hash_data(data):
            _print_change_report(
                {"has_changes": False, "checked_at": datetime.now().isoformat()},
                "JSON"
            )
            return None

        report = detect_changes(data, existing)
        _print_change_report(report, "JSON")

        if log_changes and report["has_changes"]:
            save_change_log(report)
    else:
        print(f"\n[JSON] Creating new dataset at {path}")
        report = None

    path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
    return report


def save_csv(data: list[dict], filename="dataset", path: Path | None = None, log_changes=True):
    if not data:
        raise ValueError("CSV data is empty")

    path = path or (DATA_DIR / f"{filename}.csv")
    _ensure_path(path)

    existing = _load_csv(path)

    if existing is not None:
        if _hash_data(existing) == _hash_data(data):
            _print_change_report(
                {"has_changes": False, "checked_at": datetime.now().isoformat()},
                "CSV"
            )
            return None

        report = detect_changes(data, existing)
        _print_change_report(report, "CSV")

        if log_changes and report["has_changes"]:
            save_change_log(report)
    else:
        print(f"\n[CSV] Creating new dataset at {path}")
        report = None

    keys = data[0].keys()

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

    return report


def save_txt(content: str, filename="dataset", path: Path | None = None):
    path = path or (DATA_DIR / f"{filename}.txt")
    _ensure_path(path)

    if path.exists():
        existing = _load_txt(path)
        if existing == content:
            print(f"\n[TXT] No changes — skip {path.name}")
            return False

    path.write_text(content, encoding="utf-8")
    print(f"\n[TXT] Saved {path.name}")
    return True


def save_yaml(data: Any, filename="dataset", path: Path | None = None, log_changes=True):
    path = path or (DATA_DIR / f"{filename}.yaml")
    _ensure_path(path)

    existing = _load_yaml(path)

    if existing is not None:
        if _hash_data(existing) == _hash_data(data):
            _print_change_report(
                {"has_changes": False, "checked_at": datetime.now().isoformat()},
                "YAML"
            )
            return None

        report = detect_changes(data, existing)
        _print_change_report(report, "YAML")

        if log_changes and report["has_changes"]:
            save_change_log(report)
    else:
        print(f"\n[YAML] Creating new dataset at {path}")
        report = None

    path.write_text(
        yaml.dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8"
    )

    return report