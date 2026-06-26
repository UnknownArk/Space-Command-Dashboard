import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import date
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import engine, get_db
import models
from models import Mission as DBMission, TelemetryLog, Scientist
from google import genai
from google.genai import types
from auth import create_access_token, verify_admin

#make phy tabels
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#fucking load please-env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- PYDANTIC SCHEMAS ---
class MissionCreate(BaseModel):
    name: str
    target_destination: str
    launch_date: Optional[date] = None

class ScientistResponse(BaseModel):
    id: int
    name: str
    role: str
    specialty: str
    email: str
    mission_id: Optional[int]
    bio: Optional[str]

    class Config:
        from_attributes = True

class ScientistCreate(BaseModel):
    name: str
    role: str
    specialty: str
    email: str
    bio: Optional[str] = None


# --- SECURITY ROUTE ---
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    correct_username = os.getenv("ADMIN_USERNAME")
    correct_password = os.getenv("ADMIN_PASSWORD")
    if form_data.username != correct_username or form_data.password != correct_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": form_data.username, "role": "admin"})
    return {"access_token": access_token, "token_type": "bearer"}


# --- PUBLIC ROUTES ---
@app.get("/")
def read_root():
    return {"message": "Space Exploration API is online."}

@app.get("/test-db")
def test_database(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "Success", "message": "Connected to Mysql database."}
    except:
        raise HTTPException(status_code=500, detail="DB connection failed")

@app.get("/missions")
def get_all_missions(search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(DBMission)
    if search:
        query = query.filter(DBMission.name.ilike(f"%{search}%"))
    missions = query.all()
    return {"missions": missions}

@app.get("/missions/{mission_id}")
def get_mission(mission_id: int, db: Session = Depends(get_db)):
    mission = db.query(DBMission).filter(DBMission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found.")
    return mission

@app.get("/missions/{mission_id}/telemetry")
def get_telemetry(mission_id: int, db: Session = Depends(get_db)):
    telemetry_data = db.query(TelemetryLog).filter(TelemetryLog.mission_id == mission_id).order_by(TelemetryLog.timestamp.desc()).limit(10).all()
    return {"telemetry": telemetry_data}

@app.get("/missions/{mission_id}/crew", response_model=list[ScientistResponse])
def get_mission_crew(mission_id: int, db: Session = Depends(get_db)):
    crew = db.query(Scientist).filter(Scientist.mission_id == mission_id).all()
    return crew


# --- PROTECTED ADMIN ROUTES ---
@app.post("/missions")
def create_mission(mission: MissionCreate, db: Session = Depends(get_db), admin: dict = Depends(verify_admin)):
    new_mission = DBMission(
        name=mission.name,
        target_destination=mission.target_destination,
        launch_date=mission.launch_date
    )
    db.add(new_mission)
    try:
        db.commit()
        db.refresh(new_mission)
        return {"message": "Mission Created Successfully", "mission_id": new_mission.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/missions/{mission_id}")
def update_mission(mission_id: int, mission: MissionCreate, db: Session = Depends(get_db), admin: dict = Depends(verify_admin)):
    db_mission = db.query(DBMission).filter(DBMission.id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    db_mission.name = mission.name
    db_mission.target_destination = mission.target_destination
    db_mission.launch_date = mission.launch_date

    try:
        db.commit()
        return {"message": f"Mission with {mission_id} updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/missions/{mission_id}")
def delete_mission(mission_id: int, db: Session = Depends(get_db), admin: dict = Depends(verify_admin)):
    db_mission = db.query(DBMission).filter(DBMission.id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    try:
        db.delete(db_mission)
        db.commit()
        return {"message": f"Mission with id {mission_id} is Deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/missions/{mission_id}/telemetry/fetch")
def fetch_live_telemetry(mission_id: int, db: Session = Depends(get_db), admin: dict = Depends(verify_admin)):
    try:
        iss_response = requests.get("https://api.wheretheiss.at/v1/satellites/25544")
        if iss_response.status_code != 200:
            raise HTTPException(status_code=502, detail="External telemetry uplink failed.")
            
        data = iss_response.json()
        velocity = round(data.get("velocity", 0), 2)
        altitude = round(data.get("altitude", 0), 2)
        latitude = round(data.get("latitude", 0), 4)
        
        status_level = "Nominal"
        if altitude < 408.0:
            status_level = "Warning"
            
        logs = [
            TelemetryLog(mission_id=mission_id, parameter_name="Velocity (km/h)", parameter_value=velocity, status_level="Nominal"),
            TelemetryLog(mission_id=mission_id, parameter_name="Altitude (km)", parameter_value=altitude, status_level=status_level),
            TelemetryLog(mission_id=mission_id, parameter_name="Latitude", parameter_value=latitude, status_level="Nominal")
        ]
        
        db.add_all(logs)
        db.commit()
        return {"message": "Live ISS telemetry acquired", "velocity": velocity, "altitude": altitude}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/missions/{mission_id}/analyze")
def analyze_telemetry(mission_id: int, db: Session = Depends(get_db), admin: dict = Depends(verify_admin)):
    logs = db.query(TelemetryLog).filter(TelemetryLog.mission_id == mission_id).order_by(TelemetryLog.timestamp.desc()).limit(10).all()
    if not logs:
        raise HTTPException(status_code=400, detail="Insufficient telemetry data for AI Analyze.")
    
    data_str = "\n".join([f"[{log.timestamp}] {log.parameter_name}: {log.parameter_value} ({log.status_level})" for log in logs])
    
    prompt = f"""
    You are the AI Flight Director for the A.R.E.S. aerospace relay system.
    Review the following live telemetry logs from the International Space Station (ISS):
    
    {data_str}

    Provide a concise, professional diagnostic report using Markdown. 
    Rules:
    1. Do not use outside knowledge. Only analyze the numbers provided above.
    2. Note any altitude fluctuations or velocity trends.
    3. Maximum 3 paragraphs.
    4. End the report with a strict system recommendation: [STATUS: NOMINAL] or [STATUS: WARNING].
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        return {"report": response.text}
    except Exception as e:
        print(f"\n--- FATAL AI ERROR ---\n{str(e)}\n----------------------\n")
        raise HTTPException(status_code=500, detail=f"AI Analysis failed: {str(e)}")


@app.post("/missions/{mission_id}/crew")
def add_crew_member(mission_id: int, scientist: ScientistCreate, db: Session = Depends(get_db), admin: dict = Depends(verify_admin)):
    new_scientist = Scientist(
        name=scientist.name,
        role=scientist.role,
        specialty=scientist.specialty,
        email=scientist.email,
        bio=scientist.bio,
        mission_id=mission_id
    )
    db.add(new_scientist)
    try:
        db.commit()
        return {"message": f"Successfully assigned {scientist.name} to mission: {mission_id}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error saving Crew Member: " + str(e))