#5. auth/dependencies.py — WHO is allowed
# 🔹 Purpose
# Check JWT
# Check role
# Allow / deny access
from fastapi import Depends,HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError,jwt
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # login path for token
def check_token(token:str=Depends(oauth2_scheme)):
    try:
      payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
      print(payload)
      user_role = payload.get("role")
      return user_role, payload.get("user_id")  # Return both role and user_id for further use
    except Exception as e:
      raise HTTPException(status_code=401, detail="Invalid or expired token")


