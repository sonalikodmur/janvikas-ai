"""Hotspot detection + explainable priority score. Edit WEIGHTS / HOTSPOT_MIN freely."""
import json
from collections import Counter
from .models import (Analysis, CitizenRequest, District, Infrastructure, Investment, Recommendation)

WEIGHTS = {"demand": 0.30, "infrastructure_gap": 0.25, "population": 0.20,
           "vulnerability": 0.15, "investment_gap": 0.10}  # must sum to 1.0
LABELS = {"demand": "Citizen demand", "infrastructure_gap": "Infrastructure gap",
          "population": "Population impact", "vulnerability": "Vulnerability",
          "investment_gap": "Investment gap"}
HOTSPOT_MIN = 10   # a district+category with >= this many requests is a hotspot
AFFECTED_SHARE = 0.10  # assumption: affected = population x (gap/100) x 10%
ACTIONS = {
    "Water": "Piped water scheme and tanker-dependency reduction", "Roads": "All-weather road repair and connectivity",
    "Healthcare": "Staff and equip primary health centres", "Education": "Teacher posting and school upgrades",
    "Electricity": "Feeder upgrade and voltage stabilisation", "Sanitation": "Solid-waste collection and drainage works",
    "Transport": "Regular rural bus routes to taluka towns", "Digital Connectivity": "Mobile tower and broadband expansion",
    "Agriculture": "Micro-irrigation and farmer support", "Housing": "Housing assistance for kutcha-house families",
}
LABEL_NOTE = "AI-assisted planning priority - not an official government decision."


def compute_scores(db):
    """Group requests by (district, category), score each group, flag hotspots."""
    rows = (db.query(CitizenRequest.district, Analysis.category, Analysis.severity)
            .join(Analysis, Analysis.request_pk == CitizenRequest.id).all())
    counts = Counter((d, c) for d, c, _ in rows)
    high = Counter((d, c) for d, c, s in rows if s == "High")
    if not counts: return []
    dists = {d.name: d for d in db.query(District)}
    infra = {(i.district, i.category): i.gap_score for i in db.query(Infrastructure)}
    inv = {(i.district, i.category): i.per_capita_inr for i in db.query(Investment)}
    max_inv = {}
    for (d, c), v in inv.items(): max_inv[c] = max(max_inv.get(c, 1), v)
    max_n = max(counts.values()); max_pop = max(d.population for d in dists.values())
    out = []
    for (d, c), n in counts.items():
        if d not in dists: continue
        gap = infra.get((d, c), 50.0)
        vals = {"demand": 100 * n / max_n, "infrastructure_gap": gap,
                "population": 100 * dists[d].population / max_pop,
                "vulnerability": dists[d].vulnerability,
                "investment_gap": 100 * (1 - inv.get((d, c), 0) / max_inv.get(c, 1))}
        factors = [{"name": k, "label": LABELS[k], "value": round(vals[k], 1), "weight": WEIGHTS[k],
                    "contribution": round(vals[k] * WEIGHTS[k], 1)} for k in WEIGHTS]
        out.append({"district": d, "category": c, "request_count": n, "high_severity": high[(d, c)],
                    "is_hotspot": n >= HOTSPOT_MIN, "lat": dists[d].lat, "lng": dists[d].lng,
                    "score": round(sum(f["contribution"] for f in factors), 1), "factors": factors,
                    "affected_population": int(dists[d].population * gap / 100 * AFFECTED_SHARE),
                    "note": LABEL_NOTE})
    return sorted(out, key=lambda x: -x["score"])


def refresh_recommendations(db, top=10):
    """One recommendation per hotspot (not per request), top N by score."""
    db.query(Recommendation).delete()
    for h in [g for g in compute_scores(db) if g["is_hotspot"]][:top]:
        db.add(Recommendation(
            district=h["district"], category=h["category"], score=h["score"],
            title=f"{h['category']}: {ACTIONS[h['category']]} in {h['district']}",
            action=ACTIONS[h["category"]], request_count=h["request_count"],
            affected_population=h["affected_population"], factors=json.dumps(h["factors"])))
    db.commit()
