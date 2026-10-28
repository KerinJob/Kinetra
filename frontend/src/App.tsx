import { useEffect, useState, FormEvent } from "react";
import { Link, Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { api, ApiError, Patient, Professional, Protocol, Video, fmtDate, STATUS_LABEL } from "./api";
import JobView from "./JobView";

export default function App() {
  const [me, setMe] = useState<Professional | null | undefined>(undefined);
  useEffect(() => { api.me().then(setMe).catch(() => setMe(null)); }, []);
  if (me === undefined) return <p className="center">Cargando…</p>;
  if (!me) return <Login onLogin={setMe} />;
  return (
    <>
      <header>
        <Link to="/" className="brand">Kinetra</Link>
        <span className="muted">{me.full_name}</span>
        <button className="link" onClick={async () => { await api.logout(); setMe(null); }}>Cerrar sesión</button>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Patients />} />
          <Route path="/pacientes/:id" element={<PatientDetail />} />
          <Route path="/trabajos/:id" element={<JobView />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
      <footer>
        Herramienta de apoyo a la medición. No realiza diagnóstico ni prescripción; la interpretación clínica
        corresponde al fisioterapeuta.
      </footer>
    </>
  );
}

function Login({ onLogin }: { onLogin: (p: Professional) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setErr("");
    try { onLogin(await api.login(email, password)); }
    catch (x) { setErr(x instanceof ApiError ? x.message : "Error de conexión"); }
  };
  return (
    <form className="card login" onSubmit={submit}>
      <h1>Kinetra</h1>
      <p className="muted">Acceso para profesionales</p>
      <label>Correo<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="username" /></label>
      <label>Contraseña<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" /></label>
      {err && <p className="error" role="alert">{err}</p>}
      <button type="submit">Ingresar</button>
    </form>
  );
}

function Patients() {
  const [list, setList] = useState<Patient[]>([]);
  const [q, setQ] = useState("");
  const [form, setForm] = useState({ first_name: "", last_name: "", document_id: "", phone: "" });
  const [err, setErr] = useState("");
  const nav = useNavigate();
  const load = () => api.patients(q).then(setList).catch(() => setList([]));
  useEffect(() => { load(); }, [q]);
  const create = async (e: FormEvent) => {
    e.preventDefault();
    setErr("");
    try {
      const p = await api.createPatient({
        first_name: form.first_name, last_name: form.last_name,
        document_id: form.document_id || null, phone: form.phone || null,
      });
      nav(`/pacientes/${p.id}`);
    } catch (x) { setErr(x instanceof ApiError ? x.message : "Error"); }
  };
  return (
    <div className="grid2">
      <section className="card">
        <h2>Pacientes</h2>
        <input placeholder="Buscar por nombre o documento" value={q} onChange={(e) => setQ(e.target.value)} />
        <ul className="list">
          {list.map((p) => (
            <li key={p.id}><Link to={`/pacientes/${p.id}`}>{p.last_name}, {p.first_name}</Link>
              {p.document_id && <span className="muted"> · {p.document_id}</span>}</li>
          ))}
          {list.length === 0 && <li className="muted">Sin resultados</li>}
        </ul>
      </section>
      <form className="card" onSubmit={create}>
        <h2>Nuevo paciente</h2>
        <label>Nombres<input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} required /></label>
        <label>Apellidos<input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} required /></label>
        <label>Documento (opcional)<input value={form.document_id} onChange={(e) => setForm({ ...form, document_id: e.target.value })} /></label>
        <label>Teléfono (opcional)<input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></label>
        {err && <p className="error">{err}</p>}
        <button type="submit">Registrar</button>
      </form>
    </div>
  );
}

function PatientDetail() {
  const pid = Number(useParams().id);
  const [p, setP] = useState<Patient | null>(null);
  const [videos, setVideos] = useState<Video[]>([]);
  const [protocols, setProtocols] = useState<Protocol[]>([]);
  const [proto, setProto] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const load = () => api.videos(pid).then(setVideos);
  useEffect(() => {
    api.patient(pid).then(setP).catch(() => setP(null));
    api.protocols().then((ps) => { setProtocols(ps); if (ps[0]) setProto(ps[0].code); });
    load();
  }, [pid]);
  // Sondeo mientras haya trabajos pendientes
  useEffect(() => {
    const pending = videos.some((v) => v.jobs.some((j) => j.status === "en_cola" || j.status === "procesando"));
    if (!pending) return;
    const t = setTimeout(load, 2000);
    return () => clearTimeout(t);
  }, [videos]);

  const upload = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setBusy(true); setErr("");
    try { await api.upload(pid, file, proto); setFile(null); (e.target as HTMLFormElement).reset(); await load(); }
    catch (x) { setErr(x instanceof ApiError ? x.message : "Error al subir"); }
    finally { setBusy(false); }
  };
  const selected = protocols.find((x) => x.code === proto);
  if (!p) return <p>Paciente no encontrado.</p>;
  return (
    <>
      <h2>{p.last_name}, {p.first_name}</h2>
      <p className="muted">{p.document_id ?? "Sin documento"} · Registrado {fmtDate(p.created_at)}</p>
      <form className="card" onSubmit={upload}>
        <h3>Cargar video de prueba</h3>
        <label>Prueba
          <select value={proto} onChange={(e) => setProto(e.target.value)}>
            {protocols.map((x) => <option key={x.code} value={x.code}>{x.name}</option>)}
          </select>
        </label>
        {selected && selected.validation_status.startsWith("DEMO") && (
          <p className="warn">Demostración técnica pendiente de validación profesional. No usar para decisiones clínicas.</p>
        )}
        <label>Archivo de video (mp4, mov, avi, mkv, webm)
          <input type="file" accept=".mp4,.mov,.avi,.mkv,.webm,video/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} required />
        </label>
        {err && <p className="error" role="alert">{err}</p>}
        <button type="submit" disabled={busy || !file}>{busy ? "Subiendo…" : "Subir y procesar"}</button>
      </form>
      <section className="card">
        <h3>Videos</h3>
        <table>
          <thead><tr><th>Fecha</th><th>Archivo</th><th>Duración</th><th>Prueba</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            {videos.flatMap((v) => v.jobs.map((j) => (
              <tr key={j.id}>
                <td>{fmtDate(v.created_at)}</td>
                <td>{v.original_filename}</td>
                <td>{v.duration_s.toFixed(1)} s</td>
                <td>{j.protocol_code}</td>
                <td data-testid="job-status">{STATUS_LABEL[j.status] ?? j.status}
                  {j.status === "procesando" && ` ${(j.progress * 100).toFixed(0)}%`}</td>
                <td>{j.status === "completado" && <Link to={`/trabajos/${j.id}`}>Ver resultados</Link>}
                  {j.status === "fallido" && <span className="error">{j.error}</span>}</td>
              </tr>
            )))}
            {videos.length === 0 && <tr><td colSpan={6} className="muted">Sin videos</td></tr>}
          </tbody>
        </table>
      </section>
    </>
  );
}
