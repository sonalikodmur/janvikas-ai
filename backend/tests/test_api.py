import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ.pop("GEMINI_API_KEY", None)
from fastapi.testclient import TestClient
from app.main import app


def test_flow():
    with TestClient(app) as c:
        assert c.get("/api/health").json()["status"] == "ok"
        s = c.get("/api/dashboard/summary").json()
        assert s["total_requests"] >= 500 and s["hotspot_count"] > 0
        r = c.post("/api/requests", json={"text": "No drinking water in Ward 5 for many days", "district": "Nashik"})
        assert r.status_code == 201
        rid = r.json()["request_id"]
        assert r.json()["analysis"]["category"] == "Water" and r.json()["analysis"]["severity"] == "High"
        assert c.get(f"/api/requests/{rid}").status_code == 200
        assert c.post(f"/api/requests/{rid}/analyze").status_code == 200
        assert c.get("/api/requests/nope").status_code == 404
        assert c.post("/api/requests", json={"text": "short", "district": "Nashik"}).status_code == 422
        assert c.post("/api/requests", json={"text": "long enough text here", "district": "Mars"}).status_code == 400
        h = c.get("/api/hotspots").json()["items"]
        assert h and abs(sum(f["contribution"] for f in h[0]["factors"]) - h[0]["score"]) < 0.5
        assert c.get("/api/recommendations").json()["items"]
        assert c.get("/api/requests?limit=5").json()["total"] > 500
