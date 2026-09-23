"""Evaluate labeled structured perception records without fabricating results.

Usage:
    python scripts/evaluate_vision.py
    python scripts/evaluate_vision.py --records path/to/records.json

Records must contain provenance, expected/predicted connections, and optional
expected/predicted states. Real-world metrics remain unavailable until records
with provenance=real are supplied.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.evaluation.metrics import evaluate_records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, help="JSON array of labeled evaluation records")
    args = parser.parse_args()

    records = []
    if args.records:
        with args.records.open(encoding="utf-8") as handle:
            records = json.load(handle)
        if not isinstance(records, list):
            raise SystemExit("Evaluation records must be a JSON array.")

    print(json.dumps(evaluate_records(records), indent=2))


if __name__ == "__main__":
    main()
