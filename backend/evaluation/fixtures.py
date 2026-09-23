"""Load and convert canonical, explicitly labeled Objective 2 fixtures."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "datasets" / "ldr" / "annotation.schema.json"
GOLDEN_DIR = SCHEMA_PATH.parent / "golden"


class FixtureValidationError(ValueError):
    """Raised when a fixture is missing, malformed, or violates the schema."""


def _validator() -> Draft202012Validator:
    with SCHEMA_PATH.open(encoding="utf-8") as handle:
        schema = json.load(handle)
    return Draft202012Validator(schema)


def load_fixture(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FixtureValidationError(f"Fixture does not exist: {path}")
    try:
        with path.open(encoding="utf-8") as handle:
            fixture = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise FixtureValidationError(f"Could not read fixture {path}: {exc}") from exc
    errors = sorted(_validator().iter_errors(fixture), key=lambda error: list(error.path))
    if errors:
        details = "; ".join(error.message for error in errors)
        raise FixtureValidationError(f"Invalid fixture {path.name}: {details}")
    return fixture


def load_golden_fixtures(directory: Path = GOLDEN_DIR) -> list[dict[str, Any]]:
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise FixtureValidationError(f"No golden fixtures found in {directory}")
    return [load_fixture(path) for path in paths]


def fixture_to_evaluation_record(fixture: dict[str, Any]) -> dict[str, Any]:
    """Convert canonical annotation fields to the evaluator's record shape."""
    return {
        "provenance": fixture["provenance"],
        "expected_connections": fixture.get("expected_connections", []),
        "predicted_connections": fixture.get("predicted_connections", []),
        "connection_statuses": [connection["status"] for connection in fixture.get("connections", [])],
        "expected_components": fixture.get("expected_components", []),
        "predicted_components": fixture.get("predicted_components", []),
        "expected_pins": fixture.get("expected_pins", []),
        "predicted_pins": fixture.get("predicted_pins", []),
        "expected_endpoints": fixture.get("expected_endpoints", []),
        "predicted_endpoints": fixture.get("predicted_endpoints", []),
        "expected_evidence_statuses": fixture.get("expected_evidence_statuses", []),
        "predicted_evidence_statuses": fixture.get("predicted_evidence_statuses", []),
        "expected_state": fixture["expected_state"],
        "predicted_state": fixture["predicted_state"],
    }


def load_golden_evaluation_records(directory: Path = GOLDEN_DIR) -> list[dict[str, Any]]:
    return [fixture_to_evaluation_record(fixture) for fixture in load_golden_fixtures(directory)]
