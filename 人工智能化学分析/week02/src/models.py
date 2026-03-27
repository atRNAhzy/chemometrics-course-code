from dataclasses import dataclass


@dataclass
class Paper:
    title: str = ""
    journal: str = ""
    authors: str = ""
    abstract: str = ""
    doi: str = ""
    scopus_id: str = ""
    eid: str = ""
    year: str = ""
    subtype: str = ""
    subtype_description: str = ""
    openaccess: str = ""
    source_url: str = ""
    pdf_path: str = ""
    download_status: str = ""
