import json
import yaml
from pathlib import Path


# Absolute project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

def load_json(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def index_by_model(data, key="model_name"):
    return {item[key]: item for item in data if key in item}


def merge_datasets():
    # Load datasets
    raw_data = load_json("ollama_library_raw_data.json")
    tags_data = load_json("ollama_library_raw_tags_data.json")
    latest_data = load_json("ollama_library_raw_latest_data.json")
    capabilities = load_yaml("ollama_library_capabilities.yaml")

    # Index for fast lookup
    raw_map = index_by_model(raw_data)
    tags_map = index_by_model(tags_data)
    latest_map = index_by_model(latest_data)

    merged = []

    all_model_names = set(raw_map) | set(tags_map) | set(latest_map)

    for name in all_model_names:
        model = {
            "model_name": name,

            # Base info
            "summary": raw_map.get(name, {}).get("summary"),
            "content": raw_map.get(name, {}).get("content", []),
            "metadata": raw_map.get(name, {}).get("metadata"),

            # Capabilities (NEW STRUCTURE)
            "capabilities": capabilities.get(name, []),

            # Latest
            "latest": latest_map.get(name, {}),

            # Versions
            "versions": tags_map.get(name, {}).get("versions", [])
        }

        merged.append(model)

    return merged


def save_merged(data):
    output_path = DATA_DIR / "ollama_library_merged.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"[MERGED] Saved to {output_path}")


if __name__ == "__main__":
    merged = merge_datasets()
    save_merged(merged)