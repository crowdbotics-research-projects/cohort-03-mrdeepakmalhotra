from fastapi import FastAPI, Path, Depends, HTTPException
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import MetaData
from typing import List, Dict
import json
from db.database import initialize_database, SessionLocal, engine, get_db
from models import User, Magazine, Plan, Subscription
from datetime import datetime, timedelta
from auth import create_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import secrets
from db.transactions import DBTransactions
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()
security = HTTPBearer()
initialize_database()


data_transaction = DBTransactions(engine)

from pydantic import BaseModel
class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.get("/models/")
def list_models(db: SessionLocal = Depends(get_db)):
    meta = MetaData()
    meta.reflect(bind=engine)
    tables = meta.tables.keys()
    return {"models": list(tables)}

@app.get("/models/{model_name}")
def get_model(model_name: str, db: SessionLocal = Depends(get_db)):
    meta = MetaData()
    meta.reflect(bind=engine)
    tables = meta.tables.keys()
    if model_name not in tables:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"model": model_name, "columns": list(meta.tables[model_name].columns.keys())}



@app.post("/api/register", response_model=None)
def register(username: str, email: str, password: str, address: Optional[str] = None, phone: Optional[str] = None):
    try:
        data_transaction.register(username, email, password, address, phone)
        return {"message": "User registered successfully"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error registering user")

@app.post("/api/login", response_model=None)
def login(request: LoginRequest , db: Session = Depends(get_db)):
    try:
        user = data_transaction.authenticate_user(request.email, request.password)
        if user:
            # token = create_token(user.username)
            return {"access_token": "token", "token_type": "bearer"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset-password/")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password = request.new_password  # You should hash the password before saving
    db.commit()
    return {"message": "Password reset successful"}

magazines = [
    {"name": "Magazine A", "plans": ["1", "2"], "discounts": {"1": 0.1, "2": 0.2}},
    {"name": "Magazine B", "plans": ["3", "4"], "discounts": {"3": 0.15, "4": 0.25}},
]

# @app.post("/api/magazines", response_model=None)
# def register(name: str, description: str):
#     try:
#         data_transaction.add_magazine(name, description)
#         return {"message": "magazine addedd successfully"}
#     except Exception as e:
#         print(e)
#         raise HTTPException(status_code=500, detail="Error registering user")


# @app.get("/api/magazines", response_model=None)
# def get_magazines():
#     return magazines


@app.post("/api/subscriptions", response_model=None)
def create_subscription(magazine_name: str, plan: str, user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    subscription = {"magazine_name": magazine_name, "plan": plan}
    user.subscriptions.append(subscription)
    db.add(user)  # Ensure the user instance is added to the session
    db.commit()
    return {"message": "Subscription created successfully"}

@app.get("/api/subscriptions", response_model=None)
def get_subscriptions(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user.subscriptions

@app.get("/api/subscriptions/{subscription_id}", response_model=None)
def get_subscription(subscription_id: str, db: Session = Depends(get_db)):
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return subscription

@app.delete("/api/subscriptions/{subscription_id}", response_model=None)
def cancel_subscription(subscription_id: str, db: Session = Depends(get_db)):
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    db.delete(subscription)
    db.commit()
    return {"message": "Subscription cancelled successfully"}