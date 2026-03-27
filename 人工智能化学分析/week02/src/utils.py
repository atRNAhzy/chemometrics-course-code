import re
import csv
from pathlib import Path

from src.models import Paper


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def safe_filename(text: str, limit: int = 140) -> str:
    text = re.sub(r'[\\/*?:"<>|]+', "_", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] if text else "paper"


def split_input(text: str) -> list[str]:
    if not text.strip():
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def make_keyword_folder_name(keywords: str) -> str:
    parts = split_input(keywords)
    if not parts:
        return "default"

    normalized_parts: list[str] = []
    for item in parts:
        normalized = normalize_text(item).replace(" ", "_")
        normalized = re.sub(r"_+", "_", normalized).strip("_")
        if normalized:
            normalized_parts.append(normalized)

    if not normalized_parts:
        return "default"

    folder_name = "__".join(normalized_parts)
    return folder_name[:120]


def build_query(
    keywords: str = "",
    authors: str = "",
    year_start: str = "",
    year_end: str = "",
    article_types: str = "",
) -> str:
    parts = []

    keyword_list = split_input(keywords)
    author_list = split_input(authors)
    type_list = split_input(article_types)

    if keyword_list:
        keyword_expr = " OR ".join(f'"{kw}"' for kw in keyword_list)
        parts.append(f"TITLE-ABS-KEY({keyword_expr})")

    if author_list:
        author_expr = " OR ".join(f"AUTH({author})" for author in author_list)
        parts.append(f"({author_expr})")

    if year_start:
        parts.append(f"PUBYEAR > {int(year_start) - 1}")

    if year_end:
        parts.append(f"PUBYEAR < {int(year_end) + 1}")

    if type_list:
        subtype_map = {
            "article": "ar",
            "review": "re",
            "conference paper": "cp",
            "book chapter": "ch",
        }
        subtype_codes = [
            subtype_map[item.lower()]
            for item in type_list
            if item.lower() in subtype_map
        ]
        if subtype_codes:
            subtype_expr = " OR ".join(f"SUBTYPE({code})" for code in subtype_codes)
            parts.append(f"({subtype_expr})")

    return " AND ".join(parts) if parts else 'TITLE-ABS-KEY("chemistry")'


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text


def make_paper_key(paper: Paper) -> str:
    if getattr(paper, "doi", ""):
        return f"doi:{paper.doi.lower().strip()}"

    title = normalize_text(getattr(paper, "title", ""))
    year = str(getattr(paper, "year", "")).strip()
    journal = normalize_text(getattr(paper, "journal", ""))

    return f"title:{title}|year:{year}|journal:{journal}"


def load_existing_keys(csv_path: Path) -> set[str]:
    keys: set[str] = set()
    if not csv_path.exists() or not csv_path.is_file():
        return keys

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doi = (row.get("doi") or "").strip().lower()
            if doi:
                keys.add(f"doi:{doi}")
                continue

            title = normalize_text(row.get("title") or "")
            year = (row.get("year") or "").strip()
            journal = normalize_text(row.get("journal") or "")
            keys.add(f"title:{title}|year:{year}|journal:{journal}")

    return keys
