"""AI analysis: Gemini first, keyword fallback if no key or on any failure."""
import json, os, re, urllib.request
from dotenv import load_dotenv

load_dotenv()
CATEGORIES = ["Water", "Roads", "Healthcare", "Education", "Electricity", "Sanitation",
              "Transport", "Digital Connectivity", "Agriculture", "Housing"]
SEVERITIES = ["Low", "Medium", "High"]
KEYWORDS = {
    "Water": ["water", "tanker", "पानी", "पाणी", "पाण्या"],
    "Roads": ["road", "pothole", "सड़क", "रस्ता", "रस्त्य", "खड्ड"],
    "Healthcare": ["doctor", "hospital", "clinic", "health", "अस्पताल", "डॉक्टर", "दवाखान", "रुग्णालय"],
    "Education": ["school", "teacher", "शाळा", "स्कूल", "शिक्षक"],
    "Electricity": ["power cut", "electricity", "voltage", "बिजली", "वीज"],
    "Sanitation": ["garbage", "drain", "toilet", "sewage", "कचरा", "नाली", "गटार", "शौचालय"],
    "Transport": ["bus", "transport", "बस", "एसटी"],
    "Digital Connectivity": ["internet", "network", "mobile tower", "इंटरनेट", "नेटवर्क"],
    "Agriculture": ["farm", "irrigation", "crop", "किसान", "सिंचाई", "फसल", "शेती", "शेतकरी", "सिंचन", "पिके"],
    "Housing": ["house", "housing", "घर", "आवास", "घरकुल"],
}
HIGH_WORDS = ["emergency", "dangerous", "unsafe", "died", "many days", "for months", "कई दिनों", "खतरा", "अनेक दिवस", "धोका", "महीनों"]
LOW_WORDS = ["small improvement", "minor", "थोड़ा सुधार", "थोडी सुधारणा"]


def detect_language(text):
    if re.search(r"[\u0900-\u097F]", text):
        return "mr" if re.search(r"आहे|नाही|आहेत|आमच्या|येथे|मध्ये", text) else "hi"
    return "en"


def keyword_analyze(text, hint=None):
    low = text.lower()
    scores = {c: sum(low.count(k) for k in ks) for c, ks in KEYWORDS.items()}
    best = max(scores, key=scores.get)
    matched = scores[best] > 0
    category = best if matched else (hint if hint in CATEGORIES else "Roads")
    if any(w in low for w in HIGH_WORDS): sev = "High"
    elif any(w in low for w in LOW_WORDS): sev = "Low"
    else: sev = "Medium"
    m = re.search(r"\b(?:in|at|near)\s+([A-Z][A-Za-z0-9 ]{2,30})", text)
    return {
        "language": detect_language(text), "category": category,
        "problem": re.split(r"[.।!?]", text.strip())[0][:160],
        "location": m.group(1).strip() if m else None, "severity": sev,
        "explanation": (f"Keyword rules matched '{category}' terms; severity '{sev}' from urgency words."
                        if matched else "No keywords matched; used the citizen's chosen category."),
        "source": "keyword-fallback",
    }


def validate(data, text, hint=None):
    """Make sure the AI output is safe to store; raise ValueError if unusable."""
    if not isinstance(data, dict): raise ValueError("not an object")
    if data.get("category") not in CATEGORIES: raise ValueError("bad category")
    sev = str(data.get("severity", "")).capitalize()
    if sev not in SEVERITIES: raise ValueError("bad severity")
    lang = data.get("language") if data.get("language") in ("en", "hi", "mr") else detect_language(text)
    loc = data.get("location")
    return {"language": lang, "category": data["category"], "severity": sev,
            "problem": str(data.get("problem") or text)[:300],
            "location": str(loc)[:120] if loc else None,
            "explanation": str(data.get("explanation") or "")[:400], "source": "gemini"}


def gemini_analyze(text, hint=None):
    key = os.getenv("GEMINI_API_KEY")
    if not key: return None
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    prompt = (
        "You analyse citizen development requests from India (English, Hindi or Marathi). "
        "Return ONLY JSON with keys: language (en|hi|mr), category (one of "
        f"{CATEGORIES}), problem (short English summary), location (string or null), "
        "severity (Low|Medium|High), explanation (one sentence in English).\n"
        f"Citizen's chosen category hint: {hint}\nRequest: {text}")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}}
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = json.load(r)["candidates"][0]["content"]["parts"][0]["text"]
        raw = re.sub(r"^```(?:json)?|```$", "", raw.strip()).strip()
        return validate(json.loads(raw), text, hint)
    except Exception as e:  # network, quota, bad JSON, validation ...
        print("Gemini failed, using fallback:", e)
        return None


def analyze_text(text, hint=None, use_ai=True):
    return (gemini_analyze(text, hint) if use_ai else None) or keyword_analyze(text, hint)
