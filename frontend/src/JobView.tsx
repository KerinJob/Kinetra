import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, Frame, Job, QUALITY_LABEL, fmtDate } from "./api";

const COLORS: Record<string, string> = {
  ok: "#2563eb", sin_pose: "#9ca3af", sujeto_ambiguo: "#f59e0b", baja_visibilidad: "#ef4444", angulo_invalido: "#7c3aed",
};

export default function JobView() {
  const jid = Number(useParams().id);
  const [job, setJob] = useState<Job | null>(null);
  const [frames, setFrames] = useState<Frame[]>([]);
  const [t, setT] = useState(0);
  const video = useRef<HTMLVideoElement>(null);

  useEffect(() => { api.job(jid).then(setJob); api.frames(jid).then(setFrames); }, [jid]);
  const current = useMemo(() => {
    let best: Frame | undefined;
    for (const f of frames) { if (f.timestamp_ms <= t * 1000) best = f; else break; }
    return best;
  }, [frames, t]);

  if (!job) return <p>Cargando…</p>;
  const s = job.summary;
  return (
    <>
      <p><Link to="#" onClick={() => history.back()}>← Volver</Link></p>
      <h2>Resultados · {job.protocol_code} <small className="muted">v{job.protocol_version}</small></h2>
      <p className="warn">Ángulo geométrico hombro–codo–muñeca en 2D. Demostración técnica pendiente de validación
        profesional; exactitud no establecida. No es un rango de movimiento clínico.</p>
      <div className="grid2">
        <section className="card">
          <video ref={video} src={`/api/videos/${job.video_id}/file`} controls width="100%"
                 onTimeUpdate={(e) => setT(e.currentTarget.currentTime)} />
          <p data-testid="current-angle">
            Instante {t.toFixed(2)} s: {current
              ? current.angle_deg != null ? <b>{current.angle_deg.toFixed(1)}°</b> : <b>sin medición válida</b>
              : "—"}
            {current && <span className="muted"> ({QUALITY_LABEL[current.quality] ?? current.quality})</span>}
          </p>
        </section>
        <section className="card">
          <h3>Calidad de detección</h3>
          {s && (
            <ul className="list">
              <li>Fotogramas: {s.frames_total} · válidos {(s.valid_ratio * 100).toFixed(1)}%</li>
              {Object.entries(s.frames_by_quality).map(([k, v]) => (
                <li key={k}><span className="dot" style={{ background: COLORS[k] }} />{QUALITY_LABEL[k] ?? k}: {v}</li>
              ))}
              <li>Tramo continuo más largo sin medición: {s.longest_invalid_run_frames} fotogramas</li>
              <li>Ángulo geométrico observado: {s.geometric_angle_min_deg?.toFixed(1) ?? "—"}° a {s.geometric_angle_max_deg?.toFixed(1) ?? "—"}°
                <span className="muted"> (descriptivo)</span></li>
            </ul>
          )}
          <p className="muted">Procesado {job.finished_at ? fmtDate(job.finished_at) : "—"} · motor {String(job.config?.engine_version)}
            · MediaPipe {String(job.config?.mediapipe_version)} · intentos {job.attempts}</p>
          <a href={`/api/jobs/${job.id}/frames.csv`}>Descargar serie (CSV)</a>
        </section>
      </div>
      <section className="card">
        <h3>Serie temporal</h3>
        <Chart frames={frames} cursor={t} onSeek={(s) => { if (video.current) video.current.currentTime = s; }} />
      </section>
    </>
  );
}

function Chart({ frames, cursor, onSeek }: { frames: Frame[]; cursor: number; onSeek: (s: number) => void }) {
  const W = 900, H = 260, P = 36;
  if (frames.length === 0) return <p className="muted">Sin datos</p>;
  const tMax = Math.max(frames[frames.length - 1].timestamp_ms, 1);
  const x = (ms: number) => P + ((W - 2 * P) * ms) / tMax;
  const y = (d: number) => H - P - ((H - 2 * P) * d) / 180;
  // Segmentos solo entre fotogramas válidos consecutivos: los huecos NO se interpolan.
  const segs: string[] = [];
  let cur = "";
  for (const f of frames) {
    if (f.angle_deg == null) { if (cur) segs.push(cur); cur = ""; continue; }
    cur += `${cur ? "L" : "M"}${x(f.timestamp_ms).toFixed(1)},${y(f.angle_deg).toFixed(1)}`;
  }
  if (cur) segs.push(cur);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img" aria-label="Ángulo por instante"
         onClick={(e) => {
           const r = (e.currentTarget as SVGSVGElement).getBoundingClientRect();
           const px = ((e.clientX - r.left) / r.width) * W;
           onSeek(Math.max(0, ((px - P) / (W - 2 * P)) * tMax) / 1000);
         }}>
      {[0, 45, 90, 135, 180].map((d) => (
        <g key={d}><line x1={P} x2={W - P} y1={y(d)} y2={y(d)} stroke="#e5e7eb" />
          <text x={4} y={y(d) + 4} fontSize="11">{d}°</text></g>
      ))}
      {frames.map((f) => (
        <rect key={f.frame_index} x={x(f.timestamp_ms)} y={H - P + 6} width={Math.max(1, (W - 2 * P) / frames.length)}
              height={8} fill={COLORS[f.quality] ?? "#000"} />
      ))}
      {segs.map((d, i) => <path key={i} d={d} fill="none" stroke={COLORS.ok} strokeWidth={1.5} />)}
      <line x1={x(cursor * 1000)} x2={x(cursor * 1000)} y1={P / 2} y2={H - P} stroke="#111" strokeDasharray="3 3" />
      <text x={W - P} y={H - 4} fontSize="11" textAnchor="end">{(tMax / 1000).toFixed(1)} s</text>
    </svg>
  );
}
