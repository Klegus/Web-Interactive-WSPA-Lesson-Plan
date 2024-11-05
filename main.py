import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from mangum import Mangum
from typing import List, Dict

app = FastAPI()

# Konfiguracja środowiska
if not os.environ.get("MONGO_URI"):
    from dotenv import load_dotenv
    load_dotenv()
    MONGO_URI = os.getenv("MONGO_URI")
    DEV = os.getenv("DEV")
    BACKEND_URL = os.getenv("BACKEND_URL")
else:
    MONGO_URI = os.environ.get("MONGO_URI")
    DEV = os.environ.get("DEV")
    BACKEND_URL = os.environ.get("BACKEND_URL")
    COMPARER = os.environ.get("COMPARER", "false").lower() == "true"

if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set")

# Połączenie z MongoDB
try:
    client = MongoClient(MONGO_URI)
    db = client['Lesson']
    client.admin.command('ismaster')
    print("Successfully connected to MongoDB")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    raise

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_semester_collections() -> Dict[str, Dict]:
    """
    Pobiera listę wszystkich kolekcji planów i ich najnowsze dokumenty.
    Zwraca słownik z nazwami kolekcji i odpowiadającymi im informacjami.
    """
    collections_data = {}
    for collection_name in db.list_collection_names():
        if collection_name.startswith('plans_'):
            # Pobierz najnowszy dokument z kolekcji
            latest_plan = db[collection_name].find_one(sort=[("timestamp", -1)])
            if latest_plan and "plan_name" in latest_plan and "groups" in latest_plan:
                collections_data[collection_name] = {
                    "plan_name": latest_plan["plan_name"],
                    "groups": latest_plan["groups"],
                    "timestamp": latest_plan["timestamp"]
                }
    return collections_data

@app.get("/")
async def read_root(request: Request):
    try:
        # Pobierz wszystkie dostępne plany i ich grupy
        semesters_data = get_semester_collections()
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "semesters": semesters_data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/plan/{collection_name}/{group_name}")
async def get_plan(collection_name: str, group_name: str):
    try:
        print(f"Pobieranie planu dla kolekcji: {collection_name}, grupy: {group_name}")
        latest_plan = db[collection_name].find_one(sort=[("timestamp", -1)])
        
        if not latest_plan:
            print("Nie znaleziono planu w kolekcji")
            raise HTTPException(status_code=404, detail="Plan not found")
            
        if group_name not in latest_plan["groups"]:
            print(f"Nie znaleziono grupy {group_name} w planie")
            available_groups = list(latest_plan["groups"].keys())
            print(f"Dostępne grupy: {available_groups}")
            raise HTTPException(
                status_code=404, 
                detail={
                    "message": "Nie znaleziono wybranej grupy",
                    "requested_group": group_name,
                    "available_groups": available_groups
                }
            )
        
        plan_html = latest_plan["groups"][group_name].replace('\n', '')
        #print(f"Długość pobranego HTML: {len(plan_html)}")
        #print(f"Fragment HTML: {plan_html[:200]}...")  # Pokaż początek planu
        
        response = {
            "plan_name": latest_plan["plan_name"],
            "group_name": group_name,
            "plan_html": plan_html,
            "timestamp": latest_plan["timestamp"]
        }
        print("Wysyłanie odpowiedzi:", response)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/comparisons/{collection_name}/{group_name}")
async def get_comparisons(collection_name: str, group_name: str):
    try:
        # Pobierz porównania dla konkretnego planu i grupy
        comparisons = list(db.plan_comparisons.find(
            {
                "collection_name": collection_name,
                "results." + group_name: {"$exists": True}
            },
            {
                "timestamp": 1,
                "newer_plan_timestamp": 1,
                "older_plan_timestamp": 1,
                "model_used": 1,
                "results." + group_name: 1
            }
        ).sort("timestamp", -1))
        
        if not comparisons:
            return []  # Zwróć pustą listę zamiast wyrzucać błąd
            
        for comparison in comparisons:
            comparison['_id'] = str(comparison['_id'])
        
        return comparisons
    except Exception as e:
        return []
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://37.27.207.141/status")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch status")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if DEV == 'True':
    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8000)
else:
    handler = Mangum(app)
