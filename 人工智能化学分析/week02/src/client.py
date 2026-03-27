import time
from typing import Any
from urllib.parse import quote

import requests

from src.config import (
    SCOPUS_SEARCH_URL,
    ABSTRACT_URL_BY_DOI,
    COMMON_HEADERS,
    DEFAULT_TIMEOUT,
)
from src.models import Paper


class ElsevierClient:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT, sleep_sec: float = 0.3):
        self.timeout = timeout
        self.sleep_sec = sleep_sec
        self.session = requests.Session()
        self.session.headers.update(COMMON_HEADERS)

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        response = self.session.request(
            method=method,
            url=url,
            params=params,
            timeout=self.timeout,
        )
        time.sleep(self.sleep_sec)
        return response

    def search_scopus(self, query: str, count: int = 25, start: int = 0) -> dict[str, Any]:
        params = {
            "query": query,
            "count": count,
            "start": start,
        }
        response = self._request("GET", SCOPUS_SEARCH_URL, params=params)

        if response.status_code != 200:
            raise RuntimeError(
                f"Scopus Search failed: status={response.status_code}, body={response.text[:500]}"
            )

        return response.json()

    def parse_search_results(self, payload: dict[str, Any]) -> list[Paper]:
        entries = payload.get("search-results", {}).get("entry", [])
        papers: list[Paper] = []

        for entry in entries:
            aggregation_type = entry.get("prism:aggregationType", "")
            if aggregation_type.lower() != "journal":
                continue

            title = entry.get("dc:title", "")
            journal = entry.get("prism:publicationName", "")
            authors = entry.get("dc:creator", "")
            doi = entry.get("prism:doi", "")
            scopus_id = entry.get("dc:identifier", "")
            eid = entry.get("eid", "")
            cover_date = entry.get("prism:coverDate", "")
            year = cover_date[:4] if cover_date else ""
            subtype = entry.get("subtype", "")
            subtype_description = entry.get("subtypeDescription", "")
            openaccess = str(entry.get("openaccess", ""))
            source_url = entry.get("prism:url", "")

            papers.append(
                Paper(
                    title=title,
                    journal=journal,
                    authors=authors,
                    doi=doi,
                    scopus_id=scopus_id,
                    eid=eid,
                    year=year,
                    subtype=subtype,
                    subtype_description=subtype_description,
                    openaccess=openaccess,
                    source_url=source_url,
                )
            )

        return papers

    def fetch_abstract_by_doi(self, doi: str) -> str:
        if not doi:
            return ""

        url = ABSTRACT_URL_BY_DOI.format(doi=quote(doi, safe=""))
        response = self._request("GET", url)

        if response.status_code != 200:
            return ""

        data = response.json()
        core = data.get("abstracts-retrieval-response", {}).get("coredata", {})
        return core.get("dc:description", "") or ""
