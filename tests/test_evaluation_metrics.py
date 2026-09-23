from backend.evaluation.metrics import box_iou, evaluate_records, exact_connection_metrics


def test_connection_metrics_are_deterministic():
    result = exact_connection_metrics(["LDR OUT->Arduino A0"], ["LDR OUT->Arduino A1"])
    assert result["precision"] == 0.0
    assert result["recall"] == 0.0
    assert result["wrong_or_false_connections"] == 1


def test_empty_evaluation_does_not_fabricate_metrics():
    result = evaluate_records([])
    assert result["real_world_metrics_available"] is False
    assert result["real_world"]["metrics"] is None
    assert result["real_world"]["sample_count"] == 0


def test_fixture_and_real_metrics_are_separated():
    result = evaluate_records([{
        "provenance": "test_fixture",
        "expected_connections": ["LDR OUT->Arduino A0"],
        "predicted_connections": ["LDR OUT->Arduino A0"],
        "expected_state": "PASS",
        "predicted_state": "PASS",
    }])
    assert result["test_fixture"]["sample_count"] == 1
    assert result["real_world_metrics_available"] is False
    assert result["real_world"]["reason"]


def test_entity_metric_slots_cover_components_pins_endpoints_and_statuses():
    result = evaluate_records([{
        "provenance": "test_fixture",
        "expected_components": ["LDR"],
        "predicted_components": ["LDR"],
        "expected_pins": ["LDR OUT"],
        "predicted_pins": [],
        "expected_endpoints": ["wire-1:left"],
        "predicted_endpoints": ["wire-1:left"],
        "expected_evidence_statuses": ["OBSERVED"],
        "predicted_evidence_statuses": ["UNCERTAIN"],
    }])
    entities = result["test_fixture"]["entity_metrics"]
    assert entities["components"]["recall"] == 1.0
    assert entities["pins"]["recall"] == 0.0
    assert entities["endpoints"]["precision"] == 1.0
    assert entities["evidence_statuses"]["recall"] == 0.0


def test_box_iou_uses_normalized_coordinates():
    assert box_iou({"x": 0, "y": 0, "w": 0.5, "h": 0.5}, {"x": 0, "y": 0, "w": 0.5, "h": 0.5}) == 1.0


def test_fixture_evaluation_exposes_per_record_connection_diagnostics():
    result = evaluate_records([{
        "provenance": "test_fixture",
        "expected_connections": ["LDR OUT->Arduino A0"],
        "predicted_connections": ["LDR OUT->Arduino A1"],
        "connection_statuses": ["OBSERVED"],
        "expected_state": "DEVIATION",
        "predicted_state": "DEVIATION",
    }])
    per_record = result["test_fixture"]["connection_metrics_by_record"][0]
    assert per_record["sample_count"] == 1
    assert per_record["expected_connection_detected"] is False
    assert per_record["wrong_pin_detected"] is True
    assert per_record["connection_missing"] is True
    assert result["test_fixture"]["connection_metrics_aggregate"]["sample_count"] == 1
