# ✅ 4. auth/jwt_handler.py — SECURITY (Tokens)
# 🔹 Purpose
# Create JWT
# Decode JWT
# Validate token
# ❗ No routes
# ❗ No DB models
from typing import Optional
from jose import JWTError,jwt
from dotenv import load_dotenv
import os
from datetime import datetime,timedelta

load_dotenv()
SECRET_KEY=os.getenv("JWT_SECRET_KEY")
ALGORITHM="HS256"
def create_access_token(data:dict,expires_delta : Optional [timedelta]=None):
    if not isinstance(SECRET_KEY,(str,bytes)):
      raise RuntimeError("SECRET_KEY must be set in .env and be a string or bytes")
    to_encode=data.copy()
    if  expires_delta:
      expire = datetime.utcnow() + expires_delta
    else:
     expire=datetime.utcnow()+timedelta(minutes=15)
    to_encode.update({"exp":expire})
    #to_encode.update({"role":data.get("role")})
    encode_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encode_jwt


