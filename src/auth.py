from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import secrets, string

# Secret key to encode the JWT token
SECRET_KEY = "mr-deepak-malhotra"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer expects a token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

tokens_db = {}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_token(user_id: str):
    characters = string.ascii_letters + string.digits
    # Generate a secure random string
    return ''.join(secrets.choice(characters) for _ in range(32))

def get_user_by_token(token: str):
    token_data = tokens_db.get(token)
    if token_data and token_data["expires"] > datetime.utcnow():
        return token_data["user_id"]
    return None