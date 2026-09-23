"""Metrics for structured vision outputs; no images or metrics are fabricated here."""
from __future__ import annotations

from typing import Any, Iterable

PROVENANCE = {"synthetic", "test_fixture", "real"}


def _prf(true_positive: int, false_positive: int, false_negative: int) -> dict[str, float | None]:
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = true_positive / precision_denominator if precision_denominator else None
    recall = true_positive / recall_denominator if recall_denominator else None
    f1 = (2 * precision * recall / (precision + recall)) if precision is not None and recall is not None and precision + recall else None
    return {"precision": precision, "recall": recall, "f1": f1}


def exact_connection_metrics(expected: Iterable[str], predicted: Iterable[str]) -> dict[str, Any]:
    expected_set = set(expected)
    predicted_set = set(predicted)
    true_positive = len(expected_set & predicted_set)
    return {
        "sample_count": len(expected_set),
        **_prf(true_positive, len(predicted_set - expected_set), len(expected_set - predicted_set)),
        "wrong_or_false_connections": len(predicted_set - expected_set),
    }


def classification_metrics(expected: Iterable[str], predicted: Iterable[str]) -> dict[str, Any]:
    expected_list = list(expected)
    predicted_list = list(predicted)
    if len(expected_list) != len(predicted_list):
        raise ValueError("Classification sequences must have equal length.")
    correct = sum(left == right for left, right in zip(expected_list, predicted_list))
    return {
        "sample_count": len(expected_list),
        "accuracy": correct / len(expected_list) if expected_list else None,
        "correct": correct,
        "incorrect": len(expected_list) - correct,
    }


def entity_metrics(expected: Iterable[str], predicted: Iterable[str]) -> dict[str, Any]:
    """Set-based precision/recall for components, pins, or endpoints."""
    return exact_connection_metrics(expected, predicted)


def box_iou(left: dict[str, float], right: dict[str, float]) -> float:
    """Calculate IoU for normalized x/y/w/h boxes."""
    left_x2, left_y2 = left["x"] + left["w"], left["y"] + left["h"]
    right_x2, right_y2 = right["x"] + right["w"], right["y"] + right["h"]
    intersection_width = max(0.0, min(left_x2, right_x2) - max(left["x"], right["x"]))
    intersection_height = max(0.0, min(left_y2, right_y2) - max(left["y"], right["y"]))
    intersection = intersection_width * intersection_height
    union = left["w"] * left["h"] + right["w"] * right["h"] - intersection
    return intersection / union if union else 0.0


def evaluate_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate supplied labeled records and explicitly report unavailable real metrics."""
    invalid = [record.get("provenance") for record in records if record.get("provenance") not in PROVENANCE]
    if invalid:
        raise ValueError(f"Unsupported provenance values: {invalid}")

    by_provenance: dict[str, list[dict[str, Any]]] = {name: [] for name in PROVENANCE}
    for record in records:
        by_provenance[record["provenance"]].append(record)

    def evaluate_subset(subset: list[dict[str, Any]]) -> dict[str, Any]:
        if not subset:
            return {"sample_count": 0, "metrics": None}
        connection = exact_connection_metrics(
            (connection for record in subset for connection in record.get("expected_connections", [])),
            (connection for record in subset for connection in record.get("predicted_connections", [])),
        )
        entity_results = {}
        for name in ("components", "pins", "endpoints", "evidence_statuses"):
            expected_key = f"expected_{name}"
            predicted_key = f"predicted_{name}"
            if expected_key in subset[0] or predicted_key in subset[0]:
                entity_results[name] = entity_metrics(
                    (value for record in subset for value in record.get(expected_key, [])),
                    (value for record in subset for value in record.get(predicted_key, [])),
                )
        expected_states = [record["expected_state"] for record in subset if "expected_state" in record]
        predicted_states = [record["predicted_state"] for record in subset if "predicted_state" in record]
        state_metrics = classification_metrics(expected_states, predicted_states) if len(expected_states) == len(predicted_states) else None
        false_pass = sum(record.get("predicted_state") == "PASS" and record.get("expected_state") != "PASS" for record in subset)
        false_deviation = sum(record.get("predicted_state") == "DEVIATION" and record.get("expected_state") != "DEVIATION" for record in subset)
        abstentions = sum(record.get("predicted_state") == "INSUFFICIENT_EVIDENCE" for record in subset)
        return {
            "sample_count": len(subset),
            "connection_metrics": connection,
            "entity_metrics": entity_results,
            "state_metrics": state_metrics,
            "false_pass_count": false_pass,
            "false_deviation_count": false_deviation,
            "abstention_count": abstentions,
            "abstention_rate": abstentions / len(subset),
        }

    real_records = by_provenance["real"]
    return {
        "provenance_counts": {name: len(items) for name, items in by_provenance.items()},
        "synthetic": evaluate_subset(by_provenance["synthetic"]),
        "test_fixture": evaluate_subset(by_provenance["test_fixture"]),
        "real_world_metrics_available": bool(real_records),
        "real_world": evaluate_subset(real_records) if real_records else {
            "sample_count": 0,
            "metrics": None,
            "reason": "No provenance=real photographs and annotations are present.",
        },
    }
