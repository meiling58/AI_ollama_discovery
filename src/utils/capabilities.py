from pathlib import Path
import yaml


def capabilities(data, result):
    if isinstance(data, dict):
        for value in data.values():
            capabilities(value, result)

    elif isinstance(data, list):
        for item in data:
            capabilities(item, result)

    else:
        result.append(data)

def get_capabilities():
    BASE_DIR = Path(__file__).resolve().parents[2]
    file_path = BASE_DIR / "data" / "ollama_library_capabilities.yaml"
    with open(file_path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    all_values = []
    capabilities(data, all_values)
    unique_values = list(dict.fromkeys(all_values))
    return unique_values

# print(unique_values)

# print(len(get_capabilities()))
