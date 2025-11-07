"""
Database Schemas for CampusRide

Each Pydantic model represents a MongoDB collection (lowercased class name).
Use these for request validation and data shaping across the app.
"""
from pydantic import BaseModel, Field
from typing import Optional, List

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    role: str = Field(..., description="user role: student | driver | admin")
    password: Optional[str] = Field(None, description="Plain password for demo only (not recommended)")
    is_active: bool = Field(True, description="Whether user is active")

class Driver(BaseModel):
    name: str
    phone: Optional[str] = None
    bus_id: Optional[str] = None
    license_no: Optional[str] = None
    active: bool = True

class Bus(BaseModel):
    code: str = Field(..., description="Unique bus code, e.g., BUS-101")
    route_name: str
    capacity: int = 40
    driver_id: Optional[str] = None

class Location(BaseModel):
    bus_id: str
    lat: float
    lng: float
    speed_kmh: Optional[float] = 0
    heading: Optional[float] = 0

class Announcement(BaseModel):
    title: str
    body: str
    audience: List[str] = Field(default_factory=lambda: ["student"])  # roles: student/driver/admin
