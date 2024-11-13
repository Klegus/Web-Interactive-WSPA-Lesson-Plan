import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from mangum import Mangum
from typing import List, Dict, Optional
from datetime import datetime, timedelta

app = FastAPI()

# Konfiguracja środowiska
if not os.environ.get("MONGO_URI"):
    from dotenv import load_dotenv
    load_dotenv()
    MONGO_URI = os.getenv("MONGO_URI")
    DEV = os.getenv("DEV")
    BACKEND_URL = os.getenv("BACKEND_URL")
    COMPARER = os.environ.get("COMPARER", "false").lower() == "true"

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
    db = client['Lesson_dev']
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
                    "timestamp": latest_plan["timestamp"],
                    "category": latest_plan.get("category", "st")  # Default to "st" if no category
                }
    return collections_data

@app.get("/")
async def read_root(request: Request):
    try:
        # Pobierz wszystkie dostępne plany i ich grupy
        semesters_data = get_semester_collections()
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "semesters": semesters_data,
            "show_comparer": COMPARER
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
        
        plan_html = latest_plan["groups"][group_name].replace('\n', ' ')
        #print(f"Długość pobranego HTML: {len(plan_html)}")
        #print(f"Fragment HTML: {plan_html[:200]}...")  # Pokaż początek planu
    
        response = {
            "plan_name": latest_plan["plan_name"],
            "group_name": group_name,
            "plan_html": plan_html,
            "timestamp": latest_plan["timestamp"],
            "category": latest_plan.get("category", "st")  # domyślnie "st" jeśli nie określono
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
async def get_activities(
    skip: int = 0,
    limit: int = 20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    try:
        # Podstawowa walidacja parametrów
        if limit > 50:  # Maksymalny limit
            limit = 50
        if skip < 0:
            skip = 0
            
        # Przygotowanie filtrów
        query = {}
        if start_date or end_date:
            date_filter = {}
            if start_date:
                try:
                    start_datetime = datetime.fromisoformat(start_date)
                    date_filter["$gte"] = start_datetime
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid start_date format")
            
            if end_date:
                try:
                    end_datetime = datetime.fromisoformat(end_date)
                    date_filter["$lte"] = end_datetime
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid end_date format")
            
            if date_filter:
                query["created_at"] = date_filter

        # Pobieranie dokumentów z paginacją i sortowaniem
        activities = list(db.Activities.find(
            query,
            {
                "_id": 1,
                "type": 1,
                "title": 1,
                "url": 1,
                "created_at": 1,
                "sequence_number": 1,
                "content_html": 1,
                "content_text": 1
            }
        ).sort("created_at", -1).skip(skip).limit(limit))

        # Konwersja ObjectId na string
        for activity in activities:
            activity["_id"] = str(activity["_id"])
            
        return {
            "total": db.Activities.count_documents(query),
            "activities": activities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/activities")
async def read_activities(
    skip: int = 0,
    limit: int = 20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    return await get_activities(skip, limit, start_date, end_date)

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
        uvicorn.run(app, host="0.0.0.0", port=8088)
else:
    handler = Mangum(app)
