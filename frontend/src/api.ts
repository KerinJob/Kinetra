export type Professional = { id: number; email: string; full_name: string };
export type Patient = {
  id: number; first_name: string; last_name: string; document_id: string | null;
  birth_date: string | null; phone: string | null; notes: string | null; created_at: string;
};
export type Job = {
  id: number; video_id: string; protocol_code: string; protocol_version: string; status: string;
  progress: number; attempts: number; error: string | null; summary: Summary | null;
  config: Record<string, unknown> | null; created_at: string; finished_at: string | null;
};
export type Summary = {
  frames_total: number; frames_by_quality: Record<string, number>; valid_ratio: number;
  longest_invalid_run_frames: number; geometric_angle_min_deg: number | null;
  geometric_angle_max_deg: number | null; note: string;
};
export type Video = {
  id: string; patient_id: number; original_filename: string; size_bytes: number; width: number;
  height: number; fps: number; frame_count: number; duration_s: number; created_at: string; jobs: Job[];
};
export type Frame = {
  frame_index: number; timestamp_ms: number; angle_deg: number | null; quality: string;
  min_visibility: number | null; num_poses: number;
};
export type Protocol = {
  code: string; version: string; name: string; joint: string; movement: string; side: string;
  clinical_convention: string; capture_conditions: string; validation_status: string;
};

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`/api${path}`, { credentials: "same-origin", ...init });
  if (!r.ok) {
    let msg = `Error ${r.status}`;
    try {
      const b = await r.json();
      msg = typeof b.detail === "string" ? b.detail : msg;
    } catch { /* sin cuerpo JSON */ }
    throw new ApiError(r.status, msg);
  }
  return r.status === 204 ? (undefined as T) : r.json();
}

const json = (body: unknown): RequestInit => ({
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});

export const api = {
  login: (email: string, password: string) => req<Professional>("/auth/login", json({ email, password })),
  logout: () => req<void>("/auth/logout", { method: "POST" }),
  me: () => req<Professional>("/auth/me"),
  protocols: () => req<Protocol[]>("/protocols"),
  patients: (q = "") => req<Patient[]>(`/patients${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  patient: (id: number) => req<Patient>(`/patients/${id}`),
  createPatient: (p: Partial<Patient>) => req<Patient>("/patients", json(p)),
  videos: (pid: number) => req<Video[]>(`/patients/${pid}/videos`),
  upload: (pid: number, file: File, protocol: string) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("protocol_code", protocol);
    return req<Video>(`/patients/${pid}/videos`, { method: "POST", body: fd });
  },
  job: (id: number) => req<Job>(`/jobs/${id}`),
  frames: (id: number) => req<Frame[]>(`/jobs/${id}/frames`),
};

export const TZ = "America/La_Paz";
export const fmtDate = (iso: string) =>
  new Intl.DateTimeFormat("es-BO", { timeZone: TZ, dateStyle: "short", timeStyle: "short" }).format(new Date(iso));

export const QUALITY_LABEL: Record<string, string> = {
  ok: "Válido",
  sin_pose: "Sin pose detectada",
  sujeto_ambiguo: "Más de una persona",
  baja_visibilidad: "Baja visibilidad",
  angulo_invalido: "Ángulo inválido",
};
export const STATUS_LABEL: Record<string, string> = {
  en_cola: "En cola", procesando: "Procesando", completado: "Completado", fallido: "Fallido",
};
