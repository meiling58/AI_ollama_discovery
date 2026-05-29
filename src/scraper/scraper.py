import os
from concurrent.futures import ThreadPoolExecutor
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.utils.dataset_utils import save_yaml, save_json
from src.utils.runntime_tracker import track_runtime
from src.utils.normalizers import _safe_list


class OllamaScraper:

    def __init__(self, headless=True):
        options = Options()
        if headless:
            options.add_argument("--headless")

        self.driver = webdriver.Firefox(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        self.base_url = "https://ollama.com/library"
        self.models_xpath = '//*[@id="repo"]/ul/li'
        self.max_workers = min(10, (os.cpu_count() or 2) * 2)
        self.pre_name = "ollama_library"

        # Shared session (IMPORTANT)
        self.session = self._create_session()

    # -------------------------
    # Session with retry + pool
    # -------------------------
    def _create_session(self):
        session = requests.Session()

        retries = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504]
        )

        adapter = HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=retries
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _safe_get(self, url):
        try:
            res = self.session.get(url, timeout=10)
            if res.status_code == 200:
                return res
        except Exception:
            pass
        return None

    # -------------------------
    # Selenium base
    # -------------------------
    def open_library(self):
        self.driver.get(self.base_url)
        self.driver.maximize_window()
        self.wait.until(EC.presence_of_element_located((By.ID, "repo")))

    def scroll_to_bottom(self):
        print("Scrolling to load all models...")
        last_count = 0

        while True:
            models = self.driver.find_elements(By.XPATH, self.models_xpath)
            count = len(models)

            if count == last_count:
                print("Reached the end of the library.")
                break

            last_count = count
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: len(d.find_elements(By.XPATH, self.models_xpath)) > count
                )
            except:
                break

    # -------------------------
    # Capabilities (FIXED)
    # -------------------------
    @track_runtime(engine_name="selenium")
    def get_capabilities(self) -> dict:
        model_cards = self.driver.find_elements(By.XPATH, self.models_xpath)
        model_caps = {}

        for card in model_cards:
            try:
                name = card.find_element(By.XPATH, './/h2/div/span').text

                spans = card.find_elements(
                    By.XPATH, './/div[contains(@class, "flex")]/div/span'
                )

                caps = []
                for span in spans:
                    text = span.text.strip().lower()
                    if text and not any(c.isdigit() for c in text) and text != "latest":
                        caps.append(text)

                model_caps[name] = list(set(caps))

            except Exception:
                continue

        return model_caps

    # -------------------------
    # Raw data (FIXED)
    # -------------------------
    @track_runtime(engine_name="selenium")
    def get_raw_data(self) -> list:
        model_cards = self.driver.find_elements(By.XPATH, self.models_xpath)
        raw_data = []

        for card in model_cards:
            try:
                name = card.find_element(By.XPATH, './/h2/div/span').text
                summary = card.find_element(By.XPATH, './/p').text

                content = card.find_elements(
                    By.XPATH, './/div[contains(@class, "flex")]/div'
                )[0].text.replace('\n', ' ').strip().split()

                metadata_text = card.find_element(
                    By.XPATH, './/p[contains(@class,"flex")]'
                ).text.replace('\n', ' ').strip().split()

                raw_data.append({
                    "model_name": name,
                    "summary": summary,
                    "content": content,
                    "metadata": {
                        'pulls': metadata_text[0],
                        'tags': metadata_text[2],
                        'updated': f"{metadata_text[5]} {metadata_text[6]} {metadata_text[7]}"
                    }
                })

            except Exception:
                continue

        return raw_data

    # -------------------------
    # Tags (versions)
    # -------------------------
    @track_runtime(engine_name="requests")
    def get_raw_tags_data(self) -> list:
        model_elements = self.driver.find_elements(By.XPATH, self.models_xpath)
        model_names = [
            m.find_element(By.XPATH, './/h2/div/span').text
            for m in model_elements
        ]

        def process_model(name):
            url = f"{self.base_url}/{name}/tags"
            res = self._safe_get(url)
            if not res:
                return None

            soup = BeautifulSoup(res.content, "html.parser")
            rows = soup.select("div.grid.grid-cols-12.items-center")

            versions = []

            for row in rows:
                if "bg-neutral-50" in row.get("class", []):
                    continue

                v_name_tag = row.select_one("span.col-span-6 a")
                if not v_name_tag:
                    continue

                p_cols = row.select("p.col-span-2")
                d_cols = row.select("div.col-span-2")
                sibling = row.find_next_sibling("div")

                raw = sibling.get_text(strip=True).replace("\xa0", " ") if sibling else ""

                versions.append({
                    "name": v_name_tag.text.strip(),
                    "size": p_cols[0].text.strip() if p_cols else "",
                    "context": p_cols[1].text.strip() if len(p_cols) > 1 else "",
                    "input": d_cols[-1].text.strip() if d_cols else "",
                    "usage_command": f"ollama pull {v_name_tag.text.strip()}",
                    "updated_at": raw.split("·")[-1].strip() if "·" in raw else raw
                })

            return {"model_name": name, "versions": versions}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(process_model, model_names))

        return [r for r in results if r]

    # -------------------------
    # Latest version
    # -------------------------
    @track_runtime(engine_name="requests")
    def get_latest(self) -> list:
        model_elements = self.driver.find_elements(By.XPATH, self.models_xpath)
        model_names = [
            m.find_element(By.XPATH, './/h2/div/span').text
            for m in model_elements
        ]

        def process_model(name):
            url = f"{self.base_url}/{name}"
            result = {
                "model_name": name,
                "latest": None,
                "size": None,
                "usage_command": None
            }

            res = self._safe_get(url)
            if not res:
                return result

            soup = BeautifulSoup(res.content, "html.parser")
            rows = soup.select(".border-neutral-200 a")

            for row in rows:
                data = row.text.replace('\n', ' ').strip().split()

                if len(data) >= 2 and data[1] == "latest":
                    result["latest"] = data[0]
                    result["size"] = data[2]
                    result["usage_command"] = f"ollama pull {data[0]}"
                    break

            return result

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            return list(executor.map(process_model, model_names))

    # -------------------------
    # Save all
    # -------------------------
    @track_runtime(engine_name="pipeline")
    def save_all_raw_data(self):
        self.open_library()
        self.scroll_to_bottom()

        # Capabilities (now model-level)
        caps = self.get_capabilities()
        save_yaml(caps, filename=f"{self.pre_name}_capabilities")

        # Raw data
        raw_data = self.get_raw_data()
        normalized = _safe_list(raw_data, 'model_name')
        save_json(filename=f"{self.pre_name}_raw_data", data=normalized)

        # Tags
        tags = self.get_raw_tags_data()
        save_json(filename=f"{self.pre_name}_raw_tags_data",
                  data=_safe_list(tags, 'model_name'))

        # Latest
        latest = self.get_latest()
        save_json(filename=f"{self.pre_name}_raw_latest_data",
                  data=_safe_list(latest, 'model_name'))

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    scraper = OllamaScraper()

    try:
        scraper.save_all_raw_data()

    finally:
        scraper.close()