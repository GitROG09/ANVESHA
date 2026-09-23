from backend.experiments.engine import ExperimentEngine, DEFAULT_EXPERIMENTS_DIR


def test_loads_all_experiments():
    engine = ExperimentEngine(DEFAULT_EXPERIMENTS_DIR)
    experiments = engine.list_experiments()
    assert len(experiments) >= 3
    ids = {e.experiment_id for e in experiments}
    assert "ldr_001" in ids
    assert "ultrasonic_001" in ids
    assert "led_001" in ids


def test_get_known_experiment():
    engine = ExperimentEngine(DEFAULT_EXPERIMENTS_DIR)
    exp = engine.get("ldr_001")
    assert exp.title == "LDR Light Sensor Calibration"
    assert len(exp.connections) > 0
    assert len(exp.validation_rules) > 0


def test_get_unknown_experiment_raises():
    engine = ExperimentEngine(DEFAULT_EXPERIMENTS_DIR)
    try:
        engine.get("does_not_exist")
        assert False, "expected KeyError"
    except KeyError:
        pass
