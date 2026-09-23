import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from backend.evaluation.fixtures import FixtureValidationError, load_fixture, load_golden_evaluation_records, load_golden_fixtures


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "datasets" / "ldr" / "annotation.schema.json"
GOLDEN_DIR = ROOT / "datasets" / "ldr" / "golden"


def test_every_golden_fixture_validates_against_canonical_schema():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    fixtures = load_golden_fixtures()
    assert len(fixtures) == 8
    for fixture in fixtures:
        assert list(validator.iter_errors(fixture)) == []
        assert fixture["provenance"] == "test_fixture"
        assert fixture["image_id"] is None


def test_golden_fixtures_convert_to_evaluation_records():
    records = load_golden_evaluation_records()
    assert len(records) == 8
    assert all(record["provenance"] == "test_fixture" for record in records)
    assert all("expected_state" in record and "predicted_state" in record for record in records)


def test_malformed_fixture_fails_clearly(tmp_path):
    malformed = tmp_path / "bad.json"
    malformed.write_text("{\"provenance\": \"test_fixture\"}", encoding="utf-8")
    with pytest.raises(FixtureValidationError, match="Invalid fixture"):
        load_fixture(malformed)


def test_missing_fixture_fails_clearly(tmp_path):
    with pytest.raises(FixtureValidationError, match="does not exist"):
        load_fixture(tmp_path / "missing.json")
