"""
Telemetry service — reads sensor measurements either from a real Arduino
over USB serial, or from the simulation service when no hardware is
connected. The two paths are structurally separate and every simulated
reading is tagged `simulated=True` / `source="simulated"` end to end, so
the UI can never accidentally present a simulated value as real hardware
data (a hard requirement from the project spec).

Real hardware protocol (documented, simple, and easy to reproduce with
an Arduino sketch):
    The Arduino sketch should print one line per reading to Serial as:
        <sensor_name>,<value>,<unit>\n
    e.g.
        LDR,512,ADC
        HC-SR04,37.4,cm
    at a baud rate of 115200. See scripts/arduino/telemetry_sketch.ino.
"""
from __future__ import annotations

import random
import time
from datetime import datetime, timezone

from backend.schemas.models import SensorReading

try:
    import serial  # pyserial

    _HAS_PYSERIAL = True
except ImportError:  # pragma: no cover
    _HAS_PYSERIAL = False


class ArduinoUnavailable(RuntimeError):
    pass


class TelemetryService:
    def __init__(self, port: str | None = None, baud: int = 115200):
        self.port = port
        self.baud = baud
        self._serial_conn = None

    # ---- Real hardware path -------------------------------------------------

    def connect(self) -> bool:
        if not _HAS_PYSERIAL or not self.port:
            return False
        try:
            self._serial_conn = serial.Serial(self.port, self.baud, timeout=2)
            return True
        except Exception:
            self._serial_conn = None
            return False

    def read_hardware(self, sensor: str) -> SensorReading:
        if self._serial_conn is None:
            raise ArduinoUnavailable("No Arduino serial connection established. Call connect() first or use simulation mode.")
        line = self._serial_conn.readline().decode("utf-8", errors="ignore").strip()
        if not line or "," not in line:
            raise ArduinoUnavailable(f"No valid telemetry line received from Arduino (got: {line!r}).")
        parts = line.split(",")
        if len(parts) != 3:
            raise ArduinoUnavailable(f"Malformed telemetry line from Arduino: {line!r}")
        name, value_str, unit = parts
        try:
            value = float(value_str)
        except ValueError:
            raise ArduinoUnavailable(f"Non-numeric sensor value from Arduino: {value_str!r}")
        return SensorReading(
            sensor=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(timezone.utc),
            source="arduino",
            simulated=False,
        )

    # ---- Simulation path ------------------------------------------------------

    def read_simulated(self, sensor: str, center: float, spread: float, unit: str) -> SensorReading:
        """Generate a plausible simulated reading centered on `center` with noise `spread`."""
        value = round(random.uniform(center - spread, center + spread), 2)
        return SensorReading(
            sensor=sensor,
            value=value,
            unit=unit,
            timestamp=datetime.now(timezone.utc),
            source="simulated",
            simulated=True,
        )


telemetry_service = TelemetryService()
