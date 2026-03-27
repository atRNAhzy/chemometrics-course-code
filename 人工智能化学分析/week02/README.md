# Scopus Open-Access PDF Downloader (Week02)

## Project Goal

This project searches Scopus literature through the Elsevier API, filters journal open-access papers,
tries to download PDF files, and exports records as CSV files for assignment submission.

The program keeps searching page by page and only counts successfully downloaded PDFs.

## Implemented Features

1. Scopus query with structured conditions:
- Multiple keywords (comma-separated)
- Multiple authors (optional)
- Year range (optional)
- Article subtype filter (optional)

2. Filtering strategy:
- Journal records only
- Open access only (`openaccess == 1`)
- Must have DOI before download attempt

3. PDF download strategy:
- Resolve DOI URL first
- Accept direct PDF responses
- Parse HTML for common PDF link patterns
- Save only when a valid PDF stream is detected

4. Deduplication:
- Load historical records from previous CSV files
- Use DOI as the primary unique key
- Fallback key: normalized `title + year + journal`
- Skip duplicates before download

5. Output organization:
- PDFs are saved to `outputs/pdfs/<keyword_folder>/`
- Per-keyword records are appended to `outputs/pdfs/<keyword_folder>/papers.csv`
- Global summary is written to `outputs/keyword_summary.csv`
- Summary includes `last_updated` and `new_added_this_run` for each keyword folder

## Folder Structure

```text
week02/
├── .env
├── requirements.txt
├── main.py
├── README.md
├── outputs/
│   ├── keyword_summary.csv
│   └── pdfs/
│       ├── <keyword_folder>/
│       │   ├── papers.csv
│       │   └── *.pdf
│       └── ...
└── src/
	├── __init__.py
	├── config.py
	├── models.py
	├── client.py
	├── downloader.py
	├── export.py
	└── utils.py
```

## Environment Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure API key:

Edit `.env`:

```env
ELSEVIER_API_KEY=your_api_key
```

## How To Run

```bash
python3 main.py
```

Program inputs:
1. `keywords` (comma-separated)
2. `authors` (optional)
3. `start year` (optional)
4. `end year` (optional)
5. `article types` (optional, e.g., `article,review`)
6. `target download count`

## Implementation Logic (Submission Notes)

1. Build Scopus query in `src/utils.py`:
- `build_query()` combines keyword/author/year/type expressions.

2. Search and parse in `src/client.py`:
- `search_scopus()` handles page retrieval.
- `parse_search_results()` keeps journal records and extracts metadata including subtype fields.

3. Deduplicate in `main.py`:
- Load historical keys from all `outputs/pdfs/*/papers.csv` files.
- Skip records if key already exists.

4. Download in `src/downloader.py`:
- Resolve DOI and try multiple PDF acquisition paths.
- Mark status for each attempt.

5. Export in `src/export.py`:
- Append successful records to per-keyword CSV.
- Rebuild `outputs/keyword_summary.csv` with counts for each keyword folder.
- Add `last_updated`: latest modification time of that keyword's `papers.csv`.
- Add `new_added_this_run`: how many papers were newly downloaded in the current run for that keyword.

## Notes and Limitations

1. Open access metadata does not guarantee a directly downloadable PDF on every publisher page.
2. Some websites may block automated requests or require additional access controls.
3. If not enough downloadable papers are found, the program exits gracefully with a warning.
