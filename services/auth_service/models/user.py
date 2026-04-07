
from datetime import datetime
import enum
from typing import Optional
from pydantic import BaseModel,Field


class UserRole_Schemas(str, enum.Enum):
    """Enum for user roles in the system"""
    STUDENT = "student"
    TEACHER = "teacher"
    HIGHER_TEACHER = "higher_official_teacher"
    ADMIN = "admin"

class Admin_users:
    list099=["Thenappan0732@MSDI","Muthu2321@MSDI","Muthu_P1109@MSDI"]


    """
    User model for the Local AI Study Buddy App
    
    Defines the structure of a user in the database.
    Supports multiple roles: Student, Teacher, Higher Teacher, Admin
    
    ❗ This model only handles database structure
    ❗ Authentication logic is in auth.py
    ❗ Routes are in routes/
    """
class User_Schemas(BaseModel):
    current_time_stamp:str
    user_name:str
    role:str
    user_id:str
    password:str

class Quiz_Schemas(BaseModel):
    score:Optional[int]=None
    quiz_details:Optional[dict]={}

class Note_Schemas(BaseModel):
    class_standard:Optional[str]=None
    subject:Optional[str]=None
    topic:Optional[str]=None
    note_content:str=Field(min_length=None,max_length=30000)
    log_id:Optional[str]=None
