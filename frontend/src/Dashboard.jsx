import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "./api.js";
import MapView from "./MapView.jsx";

const COLORS = ["bg-sky-600", "bg-sky-500", "bg-sky-400", "bg-blue-400", "bg-blue-300"];
const SEV = { High: "bg-red-100 text-red-700", Medium: "bg-amber-100 text-amber-700", Low: "bg-green-100 text-green-700" };

function Factors({ factors }) {
  return (
    <ul className="space-y-1 mt-2">
      {factors.map((f, i) => (
        <li key={f.name} className="text-xs">
          <div className="flex justify-between"><span>{f.label} ({Math.round(f.weight * 100)}%)</span>
            <span>{f.value} → <b>+{f.contribution}</b></span></div>
          <div className="h-1.5 bg-slate-100 rounded"><div className={`h-1.5 rounded ${COLORS[i]}`} style={{ width: `${f.value}%` }} /></div>
        </li>))}
    </ul>
  );
}

const Stat = ({ label, value }) => (<div className="card"><div className="text-xs text-slate-500">{label}</div><div className="text-2xl font-bold text-sky-800">{value}</div></div>);

export default function Dashboard() {
  const [d, setD] = useState(null), [err, setErr] = useState("");
  const [sel, setSel] = useState(null);
  const load = () => {
    setErr("");
    Promise.all([api("/api/dashboard/summary"), api("/api/hotspots"), api("/api/recommendations"), api("/api/requests?limit=8")])
      .then(([summary, hot, rec, recent]) => setD({ summary, hot, rec, recent }))
      .catch((e) => setErr(e.message));
  };
  useEffect(load, []);
  if (err) return <div role="alert" className="card text-red-700">Could not load dashboard: {err} <button className="btn ml-2" onClick={load}>Retry</button></div>;
  if (!d) return <div className="card" role="status">Loading dashboard… (the free server may take ~30 seconds to wake up)</div>;
  const { summary: s, hot, rec, recent } = d;
  return (
    <div className="space-y-6">
      <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm p-3">
        {s.data_label} All scores below are <b>AI-assisted planning priorities</b>, not official government decisions.
        <button className="ml-3 underline" onClick={load}>Refresh</button>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label="Total citizen requests" value={s.total_requests} />
        <Stat label="Demand hotspots" value={s.hotspot_count} />
        <Stat label="Est. affected population" value={s.estimated_affected_population.toLocaleString("en-IN")} />
        <Stat label="High-severity requests" value={s.by_severity.High || 0} />
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="card"><h2 className="font-bold mb-2">Requests by category</h2>
          <ResponsiveContainer width="100%" height={280}><BarChart data={s.by_category} layout="vertical" margin={{ left: 30 }}>
            <CartesianGrid strokeDasharray="3 3" /><XAxis type="number" /><YAxis type="category" dataKey="name" width={110} fontSize={11} />
            <Tooltip /><Bar dataKey="count" fill="#0284c7" /></BarChart></ResponsiveContainer></div>
        <div className="card"><h2 className="font-bold mb-2">Requests by district</h2>
          <ResponsiveContainer width="100%" height={280}><BarChart data={s.by_district} layout="vertical" margin={{ left: 40 }}>
            <CartesianGrid strokeDasharray="3 3" /><XAxis type="number" /><YAxis type="category" dataKey="name" width={140} fontSize={11} />
            <Tooltip /><Bar dataKey="count" fill="#38bdf8" /></BarChart></ResponsiveContainer></div>
      </div>
      <div className="grid md:grid-cols-3 gap-4">
        <div className="card md:col-span-2"><h2 className="font-bold mb-1">Demand hotspot map</h2>
          <p className="text-xs text-slate-500 mb-2">Click a circle. Red = priority score above 60.</p>
          <MapView hotspots={hot.items} onSelect={setSel} /></div>
        <div className="card"><h2 className="font-bold">Hotspot details</h2>
          {sel ? (<div className="text-sm mt-2"><div className="font-semibold">{sel.district} · {sel.category}</div>
            <div>Requests: <b>{sel.request_count}</b> ({sel.high_severity} high severity)</div>
            <div>Priority score: <b className="text-lg text-sky-800">{sel.score}</b>/100</div>
            <div className="text-xs text-slate-500">{sel.note}</div><Factors factors={sel.factors} /></div>)
            : <p className="text-sm text-slate-500 mt-2">Select a hotspot on the map or in the table.</p>}</div>
      </div>
      <div className="card overflow-x-auto"><h2 className="font-bold mb-1">Demand hotspots</h2>
        <p className="text-xs text-slate-500 mb-2">{hot.method}</p>
        <table className="w-full text-sm"><thead><tr className="text-left text-slate-500"><th>District</th><th>Category</th><th>Requests</th><th>Score</th></tr></thead>
          <tbody>{hot.items.slice(0, 12).map((h) => (
            <tr key={h.district + h.category} className="border-t cursor-pointer hover:bg-sky-50" onClick={() => setSel(h)}>
              <td className="py-1">{h.district}</td><td>{h.category}</td><td>{h.request_count}</td><td>{h.score}</td></tr>))}</tbody></table></div>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="card"><h2 className="font-bold mb-2">Infrastructure gaps (avg. across districts, synthetic)</h2>
          <ResponsiveContainer width="100%" height={280}><BarChart data={s.infrastructure_gaps} layout="vertical" margin={{ left: 30 }}>
            <CartesianGrid strokeDasharray="3 3" /><XAxis type="number" domain={[0, 100]} /><YAxis type="category" dataKey="name" width={110} fontSize={11} />
            <Tooltip /><Bar dataKey="gap" fill="#f59e0b" /></BarChart></ResponsiveContainer></div>
        <div className="card"><h2 className="font-bold mb-2">Recent citizen requests</h2>
          <ul className="space-y-2 max-h-[280px] overflow-auto">{recent.items.map((r) => (
            <li key={r.request_id} className="text-sm border-b pb-2">
              <div className="flex gap-2 items-center flex-wrap"><span className="font-mono text-xs">{r.request_id}</span>
                <span className={`text-xs px-2 rounded ${SEV[r.analysis.severity]}`}>{r.analysis.severity}</span>
                <span className="text-xs text-slate-500">{r.district} · {r.analysis.category} · {r.analysis.language}{r.is_synthetic ? " · synthetic" : ""}</span></div>
              <div className="text-slate-700">{r.text}</div></li>))}</ul></div>
      </div>
      <div><h2 className="font-bold text-lg mb-1">Recommended development projects</h2>
        <p className="text-xs text-slate-500 mb-2">AI-assisted planning priority · one project per hotspot · weights: {Object.entries(rec.weights).map(([k, v]) => `${k} ${v * 100}%`).join(", ")}</p>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">{rec.items.map((r, i) => (
          <div key={r.title} className="card"><div className="flex justify-between items-start gap-2">
            <div><div className="text-xs text-slate-500">#{i + 1}</div><div className="font-semibold text-sm">{r.title}</div></div>
            <div className="text-center bg-sky-100 rounded-lg px-2 py-1"><div className="text-xl font-bold text-sky-800">{r.score}</div><div className="text-[10px]">/100</div></div></div>
          <div className="text-xs text-slate-600 mt-1">{r.request_count} similar requests · ~{r.affected_population.toLocaleString("en-IN")} people (est.)</div>
          <Factors factors={r.factors} /></div>))}</div></div>
    </div>
  );
}
