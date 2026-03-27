from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
PDF_DIR = OUTPUT_DIR / "pdfs"
CSV_PATH = OUTPUT_DIR / "papers.csv"

API_KEY = os.getenv("ELSEVIER_API_KEY", "").strip()

SCOPUS_SEARCH_URL = "https://api.elsevier.com/content/search/scopus"
ABSTRACT_URL_BY_DOI = "https://api.elsevier.com/content/abstract/doi/{doi}"

DEFAULT_TIMEOUT = 30

COMMON_HEADERS = {
    "X-ELS-APIKey": API_KEY,
    "Accept": "application/json",
}

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
