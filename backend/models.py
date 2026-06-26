from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Date, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Mission(Base):
    __tablename__="missions"
    id = Column(Integer, primary_key=True,index=True)
    name= Column(String(100), nullable=False,index=True)
    target_destination=Column(String(255),nullable=False)
    status= Column(String(50),default="Planning")
    launch_date= Column(Date)
    created_at=Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    telemetry= relationship("TelemetryLog",back_populates="mission",cascade="all,delete-orphan")
    crew= relationship("Scientist",back_populates="mission")

class TelemetryLog(Base):
    __tablename__="telemetry_logs"
    id= Column(Integer,primary_key=True,index=True)
    mission_id=Column(Integer,ForeignKey("missions.id",ondelete="CASCADE"),nullable=False)
    parameter_name=Column(String(50),nullable=False)
    parameter_value=Column(Float,nullable=False)
    status_level=Column(String(50),default="Nominal")
    timestamp=Column(DateTime, default=lambda:datetime.datetime.now(datetime.timezone.utc))

    mission= relationship("Mission",back_populates="telemetry")
    __table_args__=(Index('idx_telemetry_mission_timestamp','mission_id','timestamp'),)

class Scientist(Base):
    __tablename__="scientists"
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(100),nullable=False)
    role= Column(String(100),nullable=False)
    specialty=Column(String(150),nullable=False)
    email=Column(String(100),unique=True,nullable=False)
    mission_id=Column(Integer,ForeignKey("missions.id",ondelete="SET NULL"))
    bio=Column(Text)

    mission= relationship("Mission",back_populates="crew")


