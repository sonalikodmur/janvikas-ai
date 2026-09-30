"""Synthetic demo data. ALL of this is fake - NOT real government data."""
import random
from datetime import datetime, timedelta
from .ai import CATEGORIES, keyword_analyze
from .models import Analysis, CitizenRequest, District, Infrastructure, Investment
from .planning import refresh_recommendations

# name: (lat, lng, population, vulnerability, problem categories)
DISTRICTS = {
    "Pune": (18.52, 73.86, 9430000, 30, ["Transport", "Sanitation", "Housing"]),
    "Nashik": (20.00, 73.79, 6100000, 50, ["Water", "Agriculture"]),
    "Nagpur": (21.15, 79.09, 4650000, 42, ["Sanitation", "Transport"]),
    "Chhatrapati Sambhajinagar": (19.88, 75.34, 3700000, 55, ["Water", "Roads", "Housing"]),
    "Gadchiroli": (20.18, 80.00, 1070000, 85, ["Healthcare", "Digital Connectivity", "Roads"]),
    "Nandurbar": (21.37, 74.24, 1650000, 88, ["Water", "Healthcare", "Education"]),
    "Solapur": (17.66, 75.91, 4300000, 60, ["Water", "Agriculture", "Electricity"]),
    "Kolhapur": (16.70, 74.24, 3870000, 40, ["Roads", "Agriculture"]),
}
PLACES = ["Ward 3", "Ward 7", "Gram Panchayat area", "Taluka outskirts", "Tribal hamlet"]
T = {  # {loc} and {d} are filled in below
 "Water": ("Drinking water supply has been irregular in {loc}, {d}. Families depend on tankers.", "{loc}, {d} में पीने के पानी की सप्लाई अनियमित है। परिवार टैंकर पर निर्भर हैं।", "{loc}, {d} येथे पिण्याच्या पाण्याचा पुरवठा अनियमित आहे. कुटुंबे टँकरवर अवलंबून आहेत."),
 "Roads": ("The village road near {loc}, {d} is full of potholes after rain.", "{loc}, {d} के पास की सड़क पर गड्ढे हैं।", "{loc}, {d} जवळचा रस्ता खड्ड्यांनी भरलेला आहे."),
 "Healthcare": ("There is no doctor at the nearest health clinic in {loc}, {d}.", "{loc}, {d} के नजदीकी अस्पताल में डॉक्टर नहीं हैं।", "{loc}, {d} येथील दवाखान्यात डॉक्टर उपलब्ध नाहीत."),
 "Education": ("The school in {loc}, {d} has only one teacher for five classes.", "{loc}, {d} के स्कूल में पाँच कक्षाओं के लिए एक ही शिक्षक है।", "{loc}, {d} येथील शाळेत पाच वर्गांसाठी एकच शिक्षक आहे."),
 "Electricity": ("Frequent power cuts and low voltage affect homes in {loc}, {d}.", "{loc}, {d} में बार-बार बिजली जाती है।", "{loc}, {d} येथे वारंवार वीज जाते."),
 "Sanitation": ("Garbage is not collected and open drains overflow in {loc}, {d}.", "{loc}, {d} में कचरा नहीं उठता और नाली बह रही है।", "{loc}, {d} येथे कचरा उचलला जात नाही आणि गटार तुंबले आहे."),
 "Transport": ("There is no regular bus service from {loc}, {d} to the taluka town.", "{loc}, {d} से तालुका शहर तक नियमित बस सेवा नहीं है।", "{loc}, {d} ते तालुका शहर नियमित बस सेवा नाही."),
 "Digital Connectivity": ("Mobile network and internet are very weak in {loc}, {d}.", "{loc}, {d} में मोबाइल नेटवर्क और इंटरनेट बहुत कमजोर है।", "{loc}, {d} येथे मोबाईल नेटवर्क आणि इंटरनेट खूप कमकुवत आहे."),
 "Agriculture": ("Farmers in {loc}, {d} lack irrigation and their crops are suffering.", "{loc}, {d} के किसानों को सिंचाई की सुविधा नहीं है।", "{loc}, {d} येथील शेतकऱ्यांना सिंचनाची सोय नाही."),
 "Housing": ("Many families in {loc}, {d} still live in kutcha houses and need housing support.", "{loc}, {d} में कई परिवार कच्चे घर में रहते हैं, आवास सहायता चाहिए।", "{loc}, {d} येथे अनेक कुटुंबे कच्च्या घरात राहतात, घरकुल हवे."),
}
HIGH = (" It has been like this for many days.", " कई दिनों से ऐसा है।", " अनेक दिवसांपासून असेच आहे.")
LOW = (" A small improvement would help.", " थोड़ा सुधार मददगार होगा।", " थोडी सुधारणा उपयुक्त ठरेल.")


def seed(db, n=500):
    rnd = random.Random(42)
    for name, (lat, lng, pop, vul, hot) in DISTRICTS.items():
        db.add(District(name=name, lat=lat, lng=lng, population=pop, vulnerability=vul))
        for c in CATEGORIES:
            gap = min(100, vul * 0.6 + rnd.uniform(5, 30) + (20 if c in hot else 0))
            db.add(Infrastructure(district=name, category=c, gap_score=round(gap, 1)))
            inv = rnd.uniform(300, 1500) * (1.4 - vul / 100) * (0.6 if c in hot else 1)
            db.add(Investment(district=name, category=c, per_capita_inr=round(inv, 0)))
    names = list(DISTRICTS)
    for i in range(n):
        d = rnd.choices(names, weights=[DISTRICTS[x][2] ** 0.3 for x in names])[0]
        hot = DISTRICTS[d][4]
        cat = rnd.choices(CATEGORIES, weights=[5 if c in hot else 1 for c in CATEGORIES])[0]
        li = rnd.choices([0, 1, 2], weights=[45, 30, 25])[0]
        loc = rnd.choice(PLACES)
        text = T[cat][li].format(loc=loc, d=d)
        r = rnd.random()
        text += HIGH[li] if r < 0.3 else LOW[li] if r < 0.5 else ""
        req = CitizenRequest(request_id=f"JV-SYN-{i + 1:04d}", text=text, district=d, location=loc,
                             input_mode=rnd.choice(["text", "voice"]), is_synthetic=True,
                             created_at=datetime.utcnow() - timedelta(days=rnd.randint(0, 90), minutes=rnd.randint(0, 1400)))
        a = keyword_analyze(text)
        a["explanation"] += " (synthetic demo record)"
        req.analysis = Analysis(**a)
        db.add(req)
    db.commit()
    refresh_recommendations(db)
