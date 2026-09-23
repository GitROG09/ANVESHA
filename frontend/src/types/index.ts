export interface Connection {
  from: string;
  from_pin: string;
  to: string;
  to_pin: string;
}

export interface ExpectedMeasurement {
  sensor: string;
  unit: string;
  min_value: number;
  max_value: number;
  description: string;
}

export interface ValidationRule {
  rule_id: string;
  description: string;
  rule_type: string;
  target?: string;
  severity: string;
}

export interface ExperimentStep {
  step_id: string;
  title: string;
  instruction: string;
  checks: string[];
}

export interface Experiment {
  experiment_id: string;
  title: string;
  objective: string;
  difficulty: string;
  safety_notes: string[];
  components: string[];
  connections: Connection[];
  steps: ExperimentStep[];
  expected_measurements: ExpectedMeasurement[];
  validation_rules: ValidationRule[];
  troubleshooting: Record<string, string>;
}

export interface DetectedConnection {
  from_component: string;
  from_pin: string;
  to_component: string;
  to_pin: string;
  confidence: number;
}

export interface BoundingBox {
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
  confidence: number;
  status: string;
}

export interface VisualObservation {
  sufficient_evidence: boolean;
  detected_components: string[];
  detected_connections: DetectedConnection[];
  bounding_boxes: BoundingBox[];
  notes: string;
  backend_used: string;
  simulated: boolean;
  timestamp?: string;
}

export interface SensorReading {
  sensor: string;
  value: number;
  unit: string;
  timestamp?: string;
  source: string;
  simulated: boolean;
}

export type ExperimentStateT = "PASS" | "WARNING" | "DEVIATION" | "INSUFFICIENT_EVIDENCE";

export interface StepResult {
  step_id: string;
  title: string;
  status: string;
  expected: string;
  observed: string;
  why_it_matters: string;
  recommended_action: string;
}

export interface EvidenceItem {
  source: string;
  summary: string;
}

export interface VerificationResult {
  experiment_id: string;
  experiment_state: ExperimentStateT;
  confidence: number;
  verified_steps: StepResult[];
  failed_steps: StepResult[];
  warnings: StepResult[];
  observations: string[];
  expected: string[];
  observed: string[];
  recommended_actions: string[];
  evidence: EvidenceItem[];
  timestamp?: string;
}

export interface RuntimeStatus {
  active_backend: "qualcomm-npu" | "cpu-fallback";
  vision_backend: string;
  speech_backend: string;
  device_os: string;
  device_machine: string;
  qualcomm_hardware_detected: boolean;
  notes: string;
}

export interface DemoScenario {
  id: string;
  experiment_id: string;
  description: string;
}
