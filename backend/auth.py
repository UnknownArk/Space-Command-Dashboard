import os 
import jwt
from datetime import datetime,timedelta,timezone
from fastapi import HTTPException,Depends,status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY=os.getenv("SECRET_KEY","fallback-secret")
ALGORITHM="HS256"
oauth2_scheme= OAuth2PasswordBearer(tokenUrl="login")

#Token Gen
def create_access_token(data:dict):
    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+timedelta(hours=2)
    to_encode.update({"exp":expire})
    encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

#Verifier
def verify_admin(token:str= Depends(oauth2_scheme)):
    credentials_exception=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not Validate credentials",headers={"WWW-Authenticate":"Bearer"})
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        role:str =payload.get("role")
        if role!="admin":
            raise credentials_exception
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401,detail="Token has expired. Please Log in again.")
    except jwt.InvalidTokenError:
        raise credentials_exception