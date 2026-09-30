"""JanVikas AI - FastAPI backend. Run: uvicorn app.main:app --reload"""
import json, os, secrets
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal, Optional
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func
from .ai import CATEGORIES, analyze_text
from .models import (Analysis, Base, CitizenRequest, District, Infrastructure, Recommendation,
                     SessionLocal, engine, get_db)
from .planning import HOTSPOT_MIN, LABEL_NOTE, WEIGHTS, compute_scores, refresh_recommendations
from .seed import seed


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.query(District).count() == 0:
            seed(db)  # synthetic demo data
    yield


app = FastAPI(title="JanVikas AI", version="1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in os.getenv("FRONTEND_ORIGIN", "*").split(",")],
                   allow_methods=["*"], allow_headers=["*"])


class RequestIn(BaseModel):
    text: str = Field(min_length=10, max_length=1500)
    district: str
    location: Optional[str] = Field(None, max_length=120)
    category: Optional[str] = None
    input_mode: Literal["text", "voice"] = "text"


def to_dict(r):
    a = r.analysis
    return {"request_id": r.request_id, "text": r.text, "district": r.district, "location": r.location,
            "input_mode": r.input_mode, "is_synthetic": r.is_synthetic, "created_at": r.created_at.isoformat(),
            "analysis": None if not a else {"language": a.language, "category": a.category, "problem": a.problem,
                                            "location": a.location, "severity": a.severity,
                                            "explanation": a.explanation, "source": a.source}}


def get_or_404(db, request_id):
    r = db.query(CitizenRequest).filter_by(request_id=request_id).first()
    if not r: raise HTTPException(404, "Request not found")
    return r


@app.get("/api/health")
def health(): return {"status": "ok", "time": datetime.utcnow().isoformat(), "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))}


@app.get("/api/meta")
def meta(db=Depends(get_db)):
    return {"districts": [d.name for d in db.query(District).order_by(District.name)], "categories": CATEGORIES}


@app.post("/api/requests", status_code=201)
def submit(body: RequestIn, db=Depends(get_db)):
    if not db.get(District, body.district): raise HTTPException(400, "Unknown district")
    if body.category and body.category not in CATEGORIES: raise HTTPException(400, "Unknown category")
    req = CitizenRequest(request_id=f"JV-{datetime.utcnow():%Y%m%d}-{secrets.token_hex(3).upper()}",
                         text=body.text.strip(), district=body.district, location=body.location,
                         category_hint=body.category, input_mode=body.input_mode)
    req.analysis = Analysis(**analyze_text(req.text, body.category))
    db.add(req); db.commit()
    refresh_recommendations(db)  # aggregation + scoring re-run
    return to_dict(req)


@app.get("/api/requests")
def list_requests(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
                  district: Optional[str] = None, category: Optional[str] = None, db=Depends(get_db)):
    q = db.query(CitizenRequest).join(Analysis)
    if district: q = q.filter(CitizenRequest.district == district)
    if category: q = q.filter(Analysis.category == category)
    return {"total": q.count(), "items": [to_dict(r) for r in q.order_by(CitizenRequest.created_at.desc()).offset(offset).limit(limit)]}


@app.get("/api/requests/{request_id}")
def get_request(request_id: str, db=Depends(get_db)): return to_dict(get_or_404(db, request_id))


@app.post("/api/requests/{request_id}/analyze")
def reanalyze(request_id: str, db=Depends(get_db)):
    r = get_or_404(db, request_id)
    new = analyze_text(r.text, r.category_hint)
    if r.analysis:
        for k, v in new.items(): setattr(r.analysis, k, v)
    else:
        r.analysis = Analysis(**new)
    db.commit(); refresh_recommendations(db)
    return to_dict(r)


@app.get("/api/hotspots")
def hotspots(all_groups: bool = False, db=Depends(get_db)):
    g = compute_scores(db)
    return {"hotspot_threshold": HOTSPOT_MIN, "note": LABEL_NOTE,
            "method": f"Requests grouped by district+category; a group with >= {HOTSPOT_MIN} requests is ONE hotspot (one candidate project), not one project per request.",
            "items": g if all_groups else [x for x in g if x["is_hotspot"]]}


@app.get("/api/recommendations")
def recommendations(db=Depends(get_db)):
    rows = db.query(Recommendation).order_by(Recommendation.score.desc()).all()
    return {"note": LABEL_NOTE, "weights": WEIGHTS, "items": [
        {"district": r.district, "category": r.category, "title": r.title, "action": r.action,
         "request_count": r.request_count, "score": r.score, "affected_population": r.affected_population,
         "factors": json.loads(r.factors)} for r in rows]}


@app.get("/api/dashboard/summary")
def summary(db=Depends(get_db)):
    by_cat = db.query(Analysis.category, func.count()).group_by(Analysis.category).all()
    by_dist = db.query(CitizenRequest.district, func.count()).group_by(CitizenRequest.district).all()
    gaps = db.query(Infrastructure.category, func.avg(Infrastructure.gap_score)).group_by(Infrastructure.category).all()
    sev = Counter(s for (s,) in db.query(Analysis.severity))
    recs = db.query(Recommendation).all()
    return {"total_requests": db.query(CitizenRequest).count(),
            "synthetic_requests": db.query(CitizenRequest).filter_by(is_synthetic=True).count(),
            "by_category": sorted([{"name": n, "count": c} for n, c in by_cat], key=lambda x: -x["count"]),
            "by_district": sorted([{"name": n, "count": c} for n, c in by_dist], key=lambda x: -x["count"]),
            "by_severity": dict(sev),
            "infrastructure_gaps": sorted([{"name": n, "gap": round(g, 1)} for n, g in gaps], key=lambda x: -x["gap"]),
            "hotspot_count": len(recs), "estimated_affected_population": sum(r.affected_population for r in recs),
            "affected_note": "Rough estimate from synthetic data; groups may overlap.",
            "data_label": "Demo data is SYNTHETIC and not real government data."}
