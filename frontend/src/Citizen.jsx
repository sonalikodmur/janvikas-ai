import { useEffect, useRef, useState } from "react";
import { api } from "./api.js";

const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
const VOICE_LANG = { en: "en-IN", hi: "hi-IN", mr: "mr-IN" };

export default function Citizen({ t, lang, goDash }) {
  const [meta, setMeta] = useState({ districts: [], categories: [] });
  const [f, setF] = useState({ text: "", district: "", location: "", category: "" });
  const [mode, setMode] = useState("text");
  const [listening, setListening] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [result, setResult] = useState(null);
  const rec = useRef(null), base = useRef("");

  useEffect(() => { api("/api/meta").then(setMeta).catch((e) => setErr("Cannot reach server: " + e.message)); }, []);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  function voice() {
    if (!SR) return setErr(t.noVoice);
    if (listening) return rec.current?.stop();
    setErr(""); base.current = f.text;
    const r = new SR();
    r.lang = VOICE_LANG[lang]; r.interimResults = true;
    r.onresult = (e) => {
      const s = Array.from(e.results).map((x) => x[0].transcript).join(" ");
      setF((p) => ({ ...p, text: (base.current + " " + s).trim() })); setMode("voice");
    };
    r.onerror = (e) => setErr("Voice error: " + e.error);
    r.onend = () => setListening(false);
    rec.current = r; r.start(); setListening(true);
  }

  async function submit(e) {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      const body = { text: f.text, district: f.district, input_mode: mode,
        location: f.location || null, category: f.category || null };
      setResult(await api("/api/requests", { method: "POST", body: JSON.stringify(body) }));
    } catch (x) { setErr(x.message); } finally { setBusy(false); }
  }

  if (result) {
    const a = result.analysis;
    return (
      <div className="card max-w-2xl mx-auto" role="status">
        <h2 className="text-xl font-bold text-green-700">✔ {t.done}</h2>
        <p className="mt-2">{t.yourId}: <span className="font-mono font-bold bg-sky-100 px-2 py-1 rounded">{result.request_id}</span></p>
        <h3 className="mt-4 font-semibold">{t.ai}</h3>
        <dl className="grid grid-cols-2 gap-2 text-sm mt-2">
          <dt className="text-slate-500">Category</dt><dd>{a.category}</dd>
          <dt className="text-slate-500">Severity</dt><dd>{a.severity}</dd>
          <dt className="text-slate-500">Language</dt><dd>{a.language}</dd>
          <dt className="text-slate-500">Problem</dt><dd>{a.problem}</dd>
          <dt className="text-slate-500">Explanation</dt><dd>{a.explanation}</dd>
          <dt className="text-slate-500">Analysed by</dt><dd>{a.source}</dd>
        </dl>
        <div className="mt-4 flex gap-2">
          <button className="btn" onClick={() => { setResult(null); setF({ ...f, text: "" }); }}>{t.another}</button>
          <button className="btn !bg-white !text-sky-800 border border-sky-300" onClick={goDash}>{t.dash}</button>
        </div>
      </div>
    );
  }
  return (
    <div className="grid md:grid-cols-2 gap-6 items-start">
      <section className="py-4">
        <h1 className="text-3xl font-bold text-sky-900">JanVikas AI</h1>
        <p className="mt-3 text-slate-600">{t.tagline}</p>
        <p className="mt-3 text-xs text-slate-500">Speak or type in English, Hindi or Marathi. Similar requests are grouped into demand hotspots so one shared problem becomes one planned project.</p>
      </section>
      <form onSubmit={submit} className="card space-y-3" aria-busy={busy}>
        <h2 className="font-bold text-lg">{t.form}</h2>
        <div>
          <label htmlFor="text" className="block text-sm font-semibold mb-1">{t.text}</label>
          <textarea id="text" required minLength={10} maxLength={1500} rows={5} className="input" value={f.text}
            onChange={(e) => { setF({ ...f, text: e.target.value }); setMode("text"); }} />
          <button type="button" onClick={voice} className="btn mt-2 !py-1 text-sm">🎤 {listening ? t.stop + "…" : t.voice}</button>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div><label htmlFor="d" className="block text-sm font-semibold mb-1">{t.district}</label>
            <select id="d" required className="input" value={f.district} onChange={set("district")}>
              <option value="">—</option>{meta.districts.map((d) => <option key={d}>{d}</option>)}</select></div>
          <div><label htmlFor="c" className="block text-sm font-semibold mb-1">{t.category}</label>
            <select id="c" className="input" value={f.category} onChange={set("category")}>
              <option value="">{t.auto}</option>{meta.categories.map((d) => <option key={d}>{d}</option>)}</select></div>
        </div>
        <div><label htmlFor="l" className="block text-sm font-semibold mb-1">{t.location}</label>
          <input id="l" className="input" maxLength={120} value={f.location} onChange={set("location")} /></div>
        {err && <div role="alert" className="rounded-lg bg-red-50 text-red-700 text-sm p-2">{err}</div>}
        <button className="btn w-full" disabled={busy}>{busy ? "…" : t.submit}</button>
      </form>
    </div>
  );
}
