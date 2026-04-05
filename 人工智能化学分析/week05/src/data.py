from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

RED_URLS = [
    "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv",
    "https://gitee.com/hf-datasets/wine-quality/raw/main/winequality-red.csv",
]
WHITE_URLS = [
    "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-white.csv",
    "https://gitee.com/hf-datasets/wine-quality/raw/main/winequality-white.csv",
]


def _download_if_missing(urls: list[str], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 0:
        return

    errors: list[str] = []
    for url in urls:
        try:
            urlretrieve(url, target)
            if target.exists() and target.stat().st_size > 0:
                return
        except Exception as exc:  # pragma: no cover
            errors.append(f"{url}: {exc}")

    raise RuntimeError("Failed to download dataset. Tried:\n" + "\n".join(errors))


def prepare_raw_data(red_csv: Path, white_csv: Path) -> None:
    _download_if_missing(RED_URLS, red_csv)
    _download_if_missing(WHITE_URLS, white_csv)


def load_wine_dataset(red_csv: Path, white_csv: Path) -> pd.DataFrame:
    red = pd.read_csv(red_csv, sep=";")
    white = pd.read_csv(white_csv, sep=";")
    red["wine_type"] = "red"
    white["wine_type"] = "white"
    data = pd.concat([red, white], ignore_index=True)
    return data.sample(frac=1.0, random_state=42).reset_index(drop=True)
