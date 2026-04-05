from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_dir: Path = Path(__file__).resolve().parents[1]
    data_dir: Path = project_dir / "data"
    results_dir: Path = project_dir / "results"
    random_state: int = 42
    test_size: float = 0.2

    @property
    def red_csv(self) -> Path:
        return self.data_dir / "winequality-red.csv"

    @property
    def white_csv(self) -> Path:
        return self.data_dir / "winequality-white.csv"


SETTINGS = Settings()
