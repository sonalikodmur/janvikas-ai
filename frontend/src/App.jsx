import { useState } from "react";
import Citizen from "./Citizen.jsx";
import Dashboard from "./Dashboard.jsx";
import { T } from "./i18n.js";

export default function App() {
  const [page, setPage] = useState("citizen");
  const [lang, setLang] = useState("en");
  const t = T[lang];
  const tab = (id, label) => (
    <button onClick={() => setPage(id)} aria-current={page === id ? "page" : undefined}
      className={`px-3 py-2 rounded-lg text-sm font-semibold ${page === id ? "bg-sky-700 text-white" : "text-sky-800 hover:bg-sky-100"}`}>{label}</button>
  );
  return (
    <div className="min-h-screen bg-sky-50 text-slate-800">
      <header className="bg-white border-b border-sky-100 sticky top-0 z-[1100]">
        <div className="max-w-6xl mx-auto px-4 py-3 flex flex-wrap items-center gap-3">
          <div className="mr-auto"><div className="text-xl font-bold text-sky-800">JanVikas AI</div>
            <div className="text-xs text-slate-500">Citizen-powered development planning · Digital Public Good prototype</div></div>
          <nav className="flex gap-1">{tab("citizen", t.citizen)}{tab("dash", t.dash)}</nav>
          <label className="sr-only" htmlFor="lang">Language</label>
          <select id="lang" className="input !w-auto" value={lang} onChange={(e) => setLang(e.target.value)}>
            <option value="en">English</option><option value="hi">हिन्दी</option><option value="mr">मराठी</option>
          </select>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6">
        {page === "citizen" ? <Citizen t={t} lang={lang} goDash={() => setPage("dash")} /> : <Dashboard />}
      </main>
      <footer className="text-center text-xs text-slate-500 py-6">
        Demo data is synthetic. Scores are AI-assisted planning priorities, not official government decisions.
      </footer>
    </div>
  );
}
