import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Literal
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Driver, Bus, Location, Announcement

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Helpers ----------
class LoginRequest(BaseModel):
    role: Literal["student", "driver", "admin"]
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    role: str
    user: dict

# In a production app, you'd use hashed passwords + JWT. For demo simplicity
# we simulate auth: any email/password is accepted, the role decides the view.
@app.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest):
    # upsert a user record for demonstration
    user_doc = {
        "name": req.email.split("@")[0].title(),
        "email": req.email,
        "role": req.role,
        "is_active": True,
    }
    try:
        # ensure user exists (idempotent-ish demo)
        existing = list(db["user"].find({"email": req.email}))
        if existing:
            db["user"].update_one({"_id": existing[0]["_id"]}, {"$set": user_doc})
            uid = str(existing[0]["_id"])
        else:
            uid = create_document("user", user_doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "token": f"demo-{uid}",
        "role": req.role,
        "user": {"id": uid, **user_doc},
    }

# ---------- Students: buses, drivers, locations ----------
@app.get("/buses")
def list_buses():
    buses = get_documents("bus")
    for b in buses:
        b["id"] = str(b.pop("_id"))
    return {"items": buses}

@app.get("/drivers")
def list_drivers():
    drivers = get_documents("driver")
    for d in drivers:
        d["id"] = str(d.pop("_id"))
    return {"items": drivers}

@app.get("/locations/{bus_id}")
def latest_location(bus_id: str):
    # naive latest by created_at desc
    docs = db["location"].find({"bus_id": bus_id}).sort("created_at", -1).limit(1)
    loc = next(docs, None)
    if not loc:
        return {"bus_id": bus_id, "location": None}
    loc["id"] = str(loc.pop("_id"))
    return {"bus_id": bus_id, "location": loc}

# Seed minimal demo data if collections empty
@app.get("/seed")
def seed():
    try:
        if db["bus"].count_documents({}) == 0:
            create_document("bus", {"code": "BUS-101", "route_name": "North Loop", "capacity": 50})
            create_document("bus", {"code": "BUS-202", "route_name": "South Loop", "capacity": 45})
        if db["driver"].count_documents({}) == 0:
            create_document("driver", {"name": "Amit Kumar", "phone": "+91 90000 11111", "active": True})
            create_document("driver", {"name": "Neha Sharma", "phone": "+91 98888 22222", "active": True})
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "CampusRide API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
