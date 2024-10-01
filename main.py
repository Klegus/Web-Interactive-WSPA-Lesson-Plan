# Plik: main.py

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from mangum import Mangum

app = FastAPI()

# Pobierz MongoDB URI ze zmiennej środowiskowej
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set")

try:
    client = MongoClient(MONGO_URI)
    db = client['lesson']
    # Sprawdź połączenie
    client.admin.command('ismaster')
    print("Successfully connected to MongoDB")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    raise

# Konfiguracja szablonów
templates = Jinja2Templates(directory="templates")

# Dodaj obsługę plików statycznych (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root(request: Request):
    try:
        # Pobierz listę dostępnych grup
        latest_plan = db.plans.find_one(sort=[("timestamp", -1)])
        groups = list(latest_plan["groups"].keys()) if latest_plan else []
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "groups": groups
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/plan/{group_name}")
async def get_plan(group_name: str):
    try:
        # Pobierz najnowszy plan dla wybranej grupy
        latest_plan = db.plans.find_one(sort=[("timestamp", -1)])
        if not latest_plan or group_name not in latest_plan["groups"]:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        plan_html = latest_plan["groups"][group_name]
        return {"group_name": group_name, "plan_html": plan_html, "timestamp": latest_plan["timestamp"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/comparisons/{group_name}")
async def get_comparisons(group_name: str):
    try:
        # Pobierz wszystkie porównania dla danej grupy
        comparisons = list(db.plan_comparisons.find(
            {"results." + group_name: {"$exists": True}},
            {"timestamp": 1, "newer_plan_timestamp": 1, "older_plan_timestamp": 1, "model_used": 1, "results." + group_name: 1}
        ).sort("timestamp", -1))
        
        # Konwertuj ObjectId na string dla serializacji JSON
        for comparison in comparisons:
            comparison['_id'] = str(comparison['_id'])
        
        return comparisons
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Handler dla AWS Lambda
handler = Mangum(app)