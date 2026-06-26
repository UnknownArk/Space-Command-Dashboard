from database import SessionLocal
from models import Mission  
from datetime import date

def seed_database():
    db = SessionLocal()
    
    if db.query(Mission).count() > 0:
        print("Database already contains missions. Seeding aborted.")
        db.close()
        return

    historical_missions = [
        Mission(name="Apollo 11", target_destination="Luna (Moon)", launch_date=date(1969, 7, 16), status="Terminated"),
        Mission(name="Voyager 1", target_destination="Interstellar Space", launch_date=date(1977, 9, 5), status="Active (Legacy)"),
        Mission(name="James Webb Space Telescope", target_destination="Sun-Earth L2 Lagrange Point", launch_date=date(2021, 12, 25), status="Active"),
        Mission(name="Artemis I", target_destination="Lunar Orbit", launch_date=date(2022, 11, 16), status="Terminated"),
        Mission(name="Sputnik 1", target_destination="Low Earth Orbit", launch_date=date(1957, 10, 4), status="Terminated"),
        Mission(name="Perseverance Rover", target_destination="Mars (Jezero Crater)", launch_date=date(2020, 7, 30), status="Active"),
    ]

    try:
        db.add_all(historical_missions)
        db.commit()
        print(f"Successfully injected {len(historical_missions)} historical missions into the A.R.E.S. database.")
    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()