# models.py
from pydantic import BaseModel, Field, EmailStr
from typing import List, Literal, Optional
from datetime import datetime

class RelationshipType(str):
    FRIEND = "FRIEND"
    DATED = "DATED"
    INTERACTED_WITH = "INTERACTED_WITH"

class RelationshipCreate(BaseModel):
    from_person: str
    to_person: str
    type: Literal["FRIEND", "DATED", "INTERACTED_WITH"]
    interaction_type: Optional[str] = None  # solo si INTERACTED_WITH
    timestamp: Optional[datetime] = None    # solo si INTERACTED_WITH

class InterestCreate(BaseModel):
    from_person: str
    to_person: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    age: int
    gender: str
    interests: List[str]