"""
Experiment Engine.

Loads structured experiment definitions (experiments/*.json at the repo
root) into validated Pydantic models. This is deliberately NOT an LLM
step — experiment definitions are deterministic data, and the whole point
of ANVEṢHA is that verification is grounded in explicit rules, not model
improvisation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from backend.schemas.models import Experiment

# repo_root/experiments/*.json
_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPERIMENTS_DIR = _REPO_ROOT / "experiments"


class ExperimentEngine:
    """Loads and caches experiment definitions from a directory of JSON files."""

    def __init__(self, experiments_dir: Optional[Path] = None):
        self.experiments_dir = Path(experiments_dir or DEFAULT_EXPERIMENTS_DIR)
        self._cache: dict[str, Experiment] = {}
        self._loaded = False

    def _load_all(self) -> None:
        if self._loaded:
            return
        if not self.experiments_dir.exists():
            raise FileNotFoundError(f"Experiments directory not found: {self.experiments_dir}")
        for path in sorted(self.experiments_dir.glob("*.json")):
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            exp = Experiment.model_validate(raw)
            self._cache[exp.experiment_id] = exp
        self._loaded = True

    def list_experiments(self) -> list[Experiment]:
        self._load_all()
        return list(self._cache.values())

    def get(self, experiment_id: str) -> Experiment:
        self._load_all()
        if experiment_id not in self._cache:
            raise KeyError(f"Unknown experiment_id: {experiment_id}")
        return self._cache[experiment_id]

    def reload(self) -> None:
        self._cache.clear()
        self._loaded = False
        self._load_all()


# module-level singleton used by the API layer
experiment_engine = ExperimentEngine()
