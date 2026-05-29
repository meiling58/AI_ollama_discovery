# AI_ollama_discovery

Using the Ollama Library Dataset to discover, filter and explore Ollama models with smart, real-time insights.

<details><summary>Screen shot of Ollama Models Discovery</summary>

![Ollama Models Discovery](https://github.com/meiling58/AI_ollama_discovery/blob/main/screenshot/Screenshot_Discovery_Home.png)
</details>

<details><summary>Project Structure</summary>

```
AI_ollama_discovery/
│
├── data/       # Dataset files, generated under /scraper (manually/automatically as needs) 
│   ├── ollama_library_capabilities.yaml    # created/updated after run scraper.py
│   ├── ollama_library_enriched.json        # created/updated after run enrich_dataset.py
│   ├── ollama_library_merged.json          # created/updated after run merge_datasets.py
│   ├── ollama_library_raw_data.json        # created/updated after run scraper.py
│   ├── ollama_library_raw_latest_data.json # created/updated after run scraper.py
│   └── ollama_library_raw_tags_data.json   # created/updated after run scraper.py
│
├── src/
│   ├── apps/
│       ├── __init__.py
│       ├── ollama_discovery.py
│   ├── scraper/
│       ├── __init__.py
│       ├── enrich_dataset.py
│       ├── merge_datasets.py
│       └── scraper.py
│   └── utils/
│       ├── __init__.py
│       ├── capabilities.py
│       ├── dataset_utils.py
│       ├── file_paths.py
│       ├── normalizers.py
│       └── runntime_tracker.py
|
├── .gitignore    
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```
</details>

<details><summary>Usage Instructions</summary>

1. Clone the repository.
2. Open the project in your preferred code editor, like VS Code, PyCharm, or Jupyter Notebook.
3. Navigate to the `AI_ollama_discovery` directory in your terminal.
4. Install the required dependencies using pip:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the `python -m streamlit run src/apps/ollama_discovery.py`
 script to start the application:

</details>