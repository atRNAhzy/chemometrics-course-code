import pandas as pd
from pathlib import Path
from datetime import datetime

from src.models import Paper


def export_to_csv(papers: list[Paper], csv_path: Path) -> None:
    rows = []
    for paper in papers:
        rows.append(
            {
                "title": paper.title,
                "journal": paper.journal,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "doi": paper.doi,
                "scopus_id": paper.scopus_id,
                "eid": paper.eid,
                "year": paper.year,
                "subtype": paper.subtype,
                "subtype_description": paper.subtype_description,
                "openaccess": paper.openaccess,
                "source_url": paper.source_url,
                "pdf_path": paper.pdf_path,
                "download_status": paper.download_status,
            }
        )

    if not rows:
        return

    df = pd.DataFrame(rows)
    file_exists = csv_path.exists() and csv_path.stat().st_size > 0
    df.to_csv(
        csv_path,
        index=False,
        encoding="utf-8-sig",
        mode="a" if file_exists else "w",
        header=not file_exists,
    )


def update_keyword_summary(
    summary_csv_path: Path,
    pdf_root_dir: Path,
    current_keyword: str = "",
    current_run_added: int = 0,
) -> None:
    rows: list[dict[str, int | str]] = []

    if not pdf_root_dir.exists():
        return

    for folder in sorted(pdf_root_dir.iterdir()):
        if not folder.is_dir():
            continue

        keyword_csv = folder / "papers.csv"
        if not keyword_csv.exists() or keyword_csv.stat().st_size == 0:
            continue

        try:
            df = pd.read_csv(keyword_csv)
            paper_count = len(df)
        except Exception:
            paper_count = 0

        last_updated = datetime.fromtimestamp(keyword_csv.stat().st_mtime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        new_added_this_run = current_run_added if folder.name == current_keyword else 0

        rows.append(
            {
                "keyword": folder.name,
                "paper_count": paper_count,
                "last_updated": last_updated,
                "new_added_this_run": new_added_this_run,
            }
        )

    summary_df = pd.DataFrame(
        rows,
        columns=["keyword", "paper_count", "last_updated", "new_added_this_run"],
    )
    summary_df.to_csv(summary_csv_path, index=False, encoding="utf-8-sig")
