import type {
  DemoScenario,
  Experiment,
  RuntimeStatus,
  VerificationResult,
  VisualObservation,
  SensorReading,
} from "../types";

const BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(`API error ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => req<{ status: string; service: string }>("/api/health"),

  runtime: () => req<RuntimeStatus>("/api/runtime"),

  listExperiments: () => req<Experiment[]>("/api/experiments"),

  getExperiment: (id: string) => req<Experiment>(`/api/experiments/${id}`),

  analyzeFrame: async (experimentId: string, file: Blob): Promise<VisualObservation> => {
    const form = new FormData();
    form.append("file", file, "frame.jpg");
    return req<VisualObservation>(`/api/vision/analyze?experiment_id=${encodeURIComponent(experimentId)}`, {
      method: "POST",
      body: form,
    });
  },

  simulateTelemetry: (sensor: string, center: number, spread = 5, unit = "ADC") =>
    req<SensorReading>(
      `/api/telemetry/simulate?sensor=${encodeURIComponent(sensor)}&center=${center}&spread=${spread}&unit=${encodeURIComponent(unit)}`
    ),

  verify: (experimentId: string, visualObservation: VisualObservation | null, sensorReadings: SensorReading[]) =>
    req<VerificationResult>("/api/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        experiment_id: experimentId,
        visual_observation: visualObservation,
        sensor_readings: sensorReadings,
      }),
    }),

  listDemoScenarios: () => req<DemoScenario[]>("/api/demo/scenarios"),

  runDemoScenario: (scenarioId: string) =>
    req<VerificationResult>(`/api/demo/${scenarioId}/verify`, { method: "POST" }),
};

export { BASE_URL };
