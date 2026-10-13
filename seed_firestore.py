import datetime
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-f41e5ebdaead"
db = firestore.Client(project=PROJECT_ID)

districts = [
    {
        "id": "downtown",
        "name": "Downtown Metro Core",
        "health": 68,
        "population": 120000,
        "budget": 4500000,
        "active_crises": ["Gridlock & Power Surge"],
        "status": "warning",
        "last_incident": "Transformer blowout at 5th and Main",
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    },
    {
        "id": "waterfront",
        "name": "Harbor & Waterfront District",
        "health": 88,
        "population": 65000,
        "budget": 2800000,
        "active_crises": [],
        "status": "stable",
        "last_incident": "Storm surge barrier inspection passed",
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    },
    {
        "id": "industrial",
        "name": "Eastside Industrial Park",
        "health": 42,
        "population": 35000,
        "budget": 1900000,
        "active_crises": ["Chemical Valve Leak", "Water Pipeline Pressure Drop"],
        "status": "critical",
        "last_incident": "Toxic vapor release containment underway",
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    },
    {
        "id": "highland",
        "name": "Highland Residential Hills",
        "health": 94,
        "population": 95000,
        "budget": 3200000,
        "active_crises": [],
        "status": "optimal",
        "last_incident": "Wildfire brush clearing completed",
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
]

for d in districts:
    doc_ref = db.collection("districts").document(d["id"])
    doc_ref.set(d)
    print(f"Seeded district: {d['name']}")

print("Firestore seeding complete!")
