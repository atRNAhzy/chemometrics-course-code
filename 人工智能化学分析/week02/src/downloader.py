from pathlib import Path
from urllib.parse import urljoin, unquote

import requests
from bs4 import BeautifulSoup

from src.config import BROWSER_HEADERS, DEFAULT_TIMEOUT
from src.models import Paper
from src.utils import safe_filename


class PDFDownloader:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(BROWSER_HEADERS)

    def _is_pdf_response(self, response: requests.Response) -> bool:
        content_type = response.headers.get("Content-Type", "").lower()
        return "application/pdf" in content_type

    def _save_pdf(self, response: requests.Response, paper: Paper, pdf_dir: Path) -> str:
        pdf_dir.mkdir(parents=True, exist_ok=True)
        stem = safe_filename(f"{paper.year}_{paper.title}")
        pdf_path = pdf_dir / f"{stem}.pdf"

        with open(pdf_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return str(pdf_path)

    def _candidate_links_from_html(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        candidates: list[str] = []

        selectors = [
            ("meta", {"name": "citation_pdf_url"}, "content"),
            ("meta", {"property": "citation_pdf_url"}, "content"),
            ("meta", {"name": "dc.identifier"}, "content"),
        ]

        for tag_name, attrs, attr_key in selectors:
            tag = soup.find(tag_name, attrs=attrs)
            if tag and tag.get(attr_key):
                value = tag.get(attr_key).strip()
                if value.lower().endswith(".pdf") or "/pdf" in value.lower():
                    candidates.append(urljoin(base_url, value))

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            href_lower = href.lower()
            text = a.get_text(" ", strip=True).lower()

            if (
                ".pdf" in href_lower
                or "/pdf" in href_lower
                or "pdf" in text
                or "download pdf" in text
                or "view pdf" in text
            ):
                candidates.append(urljoin(base_url, href))

        seen = set()
        unique_candidates = []
        for url in candidates:
            if url not in seen:
                seen.add(url)
                unique_candidates.append(url)

        return unique_candidates

    def _try_fetch_pdf_url(self, url: str) -> requests.Response | None:
        try:
            response = self.session.get(url, timeout=self.timeout, stream=True, allow_redirects=True)
            if response.status_code == 200 and self._is_pdf_response(response):
                return response
            response.close()
            return None
        except requests.RequestException:
            return None

    def download_openaccess_pdf(self, paper: Paper, pdf_dir: Path) -> Paper:
        if not paper.doi:
            paper.download_status = "no_doi"
            return paper

        doi_url = f"https://doi.org/{paper.doi}"

        try:
            response = self.session.get(
                doi_url,
                timeout=self.timeout,
                allow_redirects=True,
                stream=True,
            )
        except requests.RequestException:
            paper.download_status = "doi_request_error"
            return paper

        if response.status_code != 200:
            response.close()
            paper.download_status = f"doi_failed_{response.status_code}"
            return paper

        if self._is_pdf_response(response):
            paper.pdf_path = self._save_pdf(response, paper, pdf_dir)
            response.close()
            paper.download_status = "success_direct"
            return paper

        final_url = response.url
        try:
            html = response.text
        except Exception:
            html = ""
        response.close()

        candidate_links = self._candidate_links_from_html(html, final_url)

        for candidate in candidate_links:
            pdf_response = self._try_fetch_pdf_url(candidate)
            if pdf_response is not None:
                paper.pdf_path = self._save_pdf(pdf_response, paper, pdf_dir)
                pdf_response.close()
                paper.download_status = "success_from_html"
                return paper

        # 一些出版商会在 doi 跳转后 URL 本身带 pdf
        if final_url.lower().endswith(".pdf") or "/pdf" in unquote(final_url).lower():
            pdf_response = self._try_fetch_pdf_url(final_url)
            if pdf_response is not None:
                paper.pdf_path = self._save_pdf(pdf_response, paper, pdf_dir)
                pdf_response.close()
                paper.download_status = "success_from_final_url"
                return paper

        paper.download_status = "pdf_not_found"
        return paper
