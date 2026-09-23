import pytest

from backend.telemetry.service import ArduinoUnavailable, TelemetryService


def test_simulated_reading_is_tagged():
    svc = TelemetryService()
    reading = svc.read_simulated("LDR", center=500, spread=10, unit="ADC")
    assert reading.simulated is True
    assert reading.source == "simulated"
    assert 490 <= reading.value <= 510


def test_hardware_read_without_connection_raises():
    svc = TelemetryService(port=None)
    with pytest.raises(ArduinoUnavailable):
        svc.read_hardware("LDR")


def test_connect_without_port_fails_gracefully():
    svc = TelemetryService(port=None)
    assert svc.connect() is False
