from src.client import ElsevierClient
from src.config import API_KEY, OUTPUT_DIR, PDF_DIR, CSV_PATH
from src.downloader import PDFDownloader
from src.export import export_to_csv, update_keyword_summary
from src.utils import (
    ensure_dir,
    build_query,
    make_paper_key,
    load_existing_keys,
    make_keyword_folder_name,
)

PAGE_SIZE = 25
MAX_PAGES = 80  # 防止死循环


def main() -> None:
    if not API_KEY:
        raise ValueError("ELSEVIER_API_KEY is missing. Please set it in .env.")

    keywords = input("Enter keywords (comma-separated): ").strip()
    authors = input("Enter authors (comma-separated, optional): ").strip()
    year_start = input("Enter start year (optional): ").strip()
    year_end = input("Enter end year (optional): ").strip()
    article_types = input("Enter article types (comma-separated, optional): ").strip()
    target_count = int(input("Enter target download count: ").strip())

    query = build_query(
        keywords=keywords,
        authors=authors,
        year_start=year_start,
        year_end=year_end,
        article_types=article_types,
    )

    ensure_dir(OUTPUT_DIR)
    ensure_dir(PDF_DIR)

    keyword_folder = make_keyword_folder_name(keywords)
    keyword_output_dir = PDF_DIR / keyword_folder
    keyword_csv_path = keyword_output_dir / "papers.csv"
    summary_csv_path = OUTPUT_DIR / "keyword_summary.csv"
    ensure_dir(keyword_output_dir)

    client = ElsevierClient()
    downloader = PDFDownloader()

    collected: list = []
    seen_keys: set[str] = set()
    for csv_file in PDF_DIR.glob("*/papers.csv"):
        seen_keys.update(load_existing_keys(csv_file))
    seen_keys.update(load_existing_keys(CSV_PATH))
    downloaded_count = 0
    start = 0
    page_index = 0

    print(f"Searching Scopus for: {query}")
    print(f"Target open-access PDFs: {target_count}")
    print(f"Loaded existing dedup keys: {len(seen_keys)}")
    print(f"Keyword folder: {keyword_output_dir}")

    while downloaded_count < target_count and page_index < MAX_PAGES:
        print(f"\n=== Page {page_index + 1} | start={start} ===")

        payload = client.search_scopus(
            query=query,
            count=PAGE_SIZE,
            start=start,
        )

        papers = client.parse_search_results(payload)

        if not papers:
            print("No more papers returned by API.")
            break

        for paper in papers:
            if downloaded_count >= target_count:
                break

            if paper.openaccess != "1":
                continue

            if not paper.doi:
                continue

            paper_key = make_paper_key(paper)
            if paper_key in seen_keys:
                continue

            seen_keys.add(paper_key)

            print(f"Trying DOI: {paper.doi}")
            print(f"Title: {paper.title}")

            if not paper.abstract:
                paper.abstract = client.fetch_abstract_by_doi(paper.doi)

            paper = downloader.download_openaccess_pdf(paper, keyword_output_dir)

            print(f"Download status: {paper.download_status}")

            if paper.download_status.startswith("success"):
                collected.append(paper)
                downloaded_count += 1
                print(f"Downloaded {downloaded_count}/{target_count}")

        start += PAGE_SIZE
        page_index += 1

    export_to_csv(collected, keyword_csv_path)
    update_keyword_summary(
        summary_csv_path,
        PDF_DIR,
        current_keyword=keyword_folder,
        current_run_added=downloaded_count,
    )

    print("\n===== Finished =====")
    print(f"Downloaded PDFs: {downloaded_count}")
    print(f"Keyword CSV saved to: {keyword_csv_path}")
    print(f"PDF folder: {keyword_output_dir}")
    print(f"Summary CSV saved to: {summary_csv_path}")

    if downloaded_count < target_count:
        print(
            f"Warning: fewer than {target_count} downloadable OA PDFs were found within current search range."
        )


if __name__ == "__main__":
    main()
