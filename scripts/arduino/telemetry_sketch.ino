/*
  ANVEṢHA AI — Telemetry Sketch

  Implements the serial protocol expected by backend/telemetry/service.py:
    <sensor_name>,<value>,<unit>\n
  at 115200 baud, one reading per line.

  This sketch supports the three experiments shipped in experiments/*.json.
  Uncomment the block matching your current experiment, or extend as needed.
  Only one experiment's sensor should be active at a time to match what the
  UI expects to read.

  NOT executed or tested against real hardware as part of building this
  repository snapshot (no Arduino was available in the development
  environment) — see docs/limitations.md. Verify pin numbers against your
  actual wiring before relying on this for a live demo.
*/

const unsigned long BAUD_RATE = 115200;
const unsigned long SEND_INTERVAL_MS = 500;

// ---- Select ONE experiment by uncommenting its #define ----
#define EXPERIMENT_LDR
// #define EXPERIMENT_ULTRASONIC
// #define EXPERIMENT_LED

#ifdef EXPERIMENT_LDR
const int LDR_PIN = A0;
#endif

#ifdef EXPERIMENT_ULTRASONIC
const int TRIG_PIN = 9;
const int ECHO_PIN = 10;
#endif

#ifdef EXPERIMENT_LED
const int LED_PIN = 8;
const int CURRENT_SENSE_PIN = A1; // optional: via a small sense resistor
#endif

unsigned long lastSend = 0;

void setup() {
  Serial.begin(BAUD_RATE);
#ifdef EXPERIMENT_ULTRASONIC
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
#endif
#ifdef EXPERIMENT_LED
  pinMode(LED_PIN, OUTPUT);
#endif
}

void loop() {
  unsigned long now = millis();
  if (now - lastSend < SEND_INTERVAL_MS) return;
  lastSend = now;

#ifdef EXPERIMENT_LDR
  int raw = analogRead(LDR_PIN); // 0-1023
  Serial.print("LDR,");
  Serial.print(raw);
  Serial.println(",ADC");
#endif

#ifdef EXPERIMENT_ULTRASONIC
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000UL); // 30ms timeout ~ 5m range
  float distance_cm = duration * 0.0343 / 2.0;

  Serial.print("HC-SR04,");
  Serial.print(distance_cm);
  Serial.println(",cm");
#endif

#ifdef EXPERIMENT_LED
  digitalWrite(LED_PIN, HIGH);
  delay(50); // allow current to settle
  int senseRaw = analogRead(CURRENT_SENSE_PIN);
  // Placeholder conversion — calibrate against your actual sense resistor value.
  float current_mA = senseRaw * (5.0 / 1023.0) / 220.0 * 1000.0;

  Serial.print("LED_current,");
  Serial.print(current_mA);
  Serial.println(",mA");
#endif
}
