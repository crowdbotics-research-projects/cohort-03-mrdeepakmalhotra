from fastapi import FastAPI, Path, Depends, HTTPException, Security
from typing import Optional
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import MetaData
from typing import List, Dict
import json
from db.database import initialize_database, SessionLocal, engine, get_db
from models import User, Magazine, Plan, Subscription
from datetime import datetime, timedelta
from auth import verify_password, create_access_token, create_refresh_token, verify_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import secrets
from db.transactions import DBTransactions
from pydantic import BaseModel, EmailStr
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()
security = HTTPBearer()
initialize_database()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    phone: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str

class LoginRequest(BaseModel):
    username: str
    password: str

# Pydantic model for creating a magazine
class MagazineCreate(BaseModel):
    name: str
    description: str
    base_price: float
    discount_quarterly: float
    discount_half_yearly: float
    discount_annual: float

class PlanModel(BaseModel):
    title: str
    description: str
    renewal_period: int

class PlanResponse(BaseModel):
    id: int
    title: str
    description: str
    renewal_period: int

class SubscriptionCreate(BaseModel):
    user_id: int
    magazine_id: int
    plan_id: int
    price: float
    # price_at_renewal: int
    next_renewal_date: datetime

    class Config:
        orm_mode = True

class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    magazine_id: int
    plan_id: int
    price: float
    price_at_renewal: float
    next_renewal_date: datetime
    is_active: bool

data_transaction = DBTransactions(engine)

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

@app.post("/users/register", response_model=None)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        db_user = User(**request.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error registering user")

@app.post("/users/login", response_model=None)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == request.username).first()
        if user and verify_password(request.password, user.password):
            access_token = create_access_token({"sub": user.username})
            refresh_token = create_refresh_token({"sub": user.username})
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "status_code": 200,
                "text": "Success"
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/reset-password")
def reset_password(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    reset_token = create_refresh_token({"sub": user.username})  # Replace with actual token generation logic
    print(f"Generated reset token for {user.email}: {reset_token}")
    return {"message": "Password reset email sent"}

@app.post("/users/token/refresh")
def user_token_refresh(token: str = Security(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    refresh_token = create_refresh_token({"sub": user.username})  # Replace with actual token generation logic
    access_token = create_access_token({"sub": user.username})
    return {"refresh_token": refresh_token, "access_token": access_token}


@app.get("/users/me")
def verify_user_token(token: str = Security(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    print(payload)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username, "status": 200}

@app.delete("/users/deactivate/{username}")
def deactivate_user(username: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.is_active = False  # Assuming there is an `is_active` field in the User model
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/magazines/", response_model=None)
def create_magazine(magazine: MagazineCreate, db: Session = Depends(get_db)):
    db_magazine = Magazine(**magazine.dict())
    db.add(db_magazine)
    db.commit()
    db.refresh(db_magazine)
    return db_magazine

@app.get("/magazines/", response_model=List[MagazineCreate])
def get_magazines(db: Session = Depends(get_db)):
    try:
        magazines = db.query(Magazine).all()
        return magazines
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.put("/magazines/{magazine_id}", response_model=MagazineCreate)
def update_magazine(magazine_id: int, magazine: MagazineCreate, db: Session = Depends(get_db)):
    db_magazine = db.query(Magazine).filter(Magazine.id == magazine_id).first()
    if db_magazine is None:
        raise HTTPException(status_code=404, detail="Magazine not found")
    
    for key, value in magazine.dict().items():
        setattr(db_magazine, key, value)
    
    db.commit()
    db.refresh(db_magazine)
    return db_magazine

@app.delete("/magazines/{magazine_id}", response_model=MagazineCreate)
def delete_magazine(magazine_id: int, db: Session = Depends(get_db)):
    db_magazine = db.query(Magazine).filter(Magazine.id == magazine_id).first()
    if db_magazine is None:
        raise HTTPException(status_code=404, detail="Magazine not found")
    
    db.delete(db_magazine)
    db.commit()
    return db_magazine

@app.get("/magazines/{magazine_id}", response_model=MagazineCreate)
def get_magazine_by_id(magazine_id: int, db: Session = Depends(get_db)):
    db_magazine = db.query(Magazine).filter(Magazine.id == magazine_id).first()
    if db_magazine is None:
        raise HTTPException(status_code=404, detail="Magazine not found")
    return db_magazine

@app.post("/plans/", response_model=PlanResponse)
def create_plan(plan: PlanModel, db: Session = Depends(get_db)):
    if plan.renewal_period == 0:
        raise HTTPException(status_code=422, detail="Renewal period cannot be zero")
    db_plan = Plan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

@app.get("/plans/", response_model=List[PlanResponse])
def get_all_plans(db: Session = Depends(get_db)):
    plans = db.query(Plan).all()
    return plans

@app.put("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(plan_id: int, plan: PlanModel, db: Session = Depends(get_db)):
    db_plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if db_plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    for key, value in plan.dict().items():
        setattr(db_plan, key, value)
    
    db.commit()
    db.refresh(db_plan)
    return db_plan

@app.delete("/plans/{plan_id}", response_model=PlanResponse)
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    db_plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if db_plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    db.delete(db_plan)
    db.commit()
    return db_plan

@app.get("/plans/{plan_id}", response_model=PlanResponse)
def get_magazine_by_id(plan_id: int, db: Session = Depends(get_db)):
    db_plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if db_plan is None:
        raise HTTPException(status_code=404, detail="Magazine not found")
    return db_plan

@app.post("/subscriptions/", response_model=SubscriptionResponse)
def create_subscription(subscription: SubscriptionCreate, db: Session = Depends(get_db)):
    db_subscription = Subscription(**subscription.dict())
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription

@app.get("/subscriptions/", response_model=List[SubscriptionResponse])
def get_all_subscriptions(db: Session = Depends(get_db)):
    subs = db.query(Subscription).all()
    return subs

@app.put("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(subscription_id: int, subscription: SubscriptionCreate, db: Session = Depends(get_db)):
    db_subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if db_subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    for key, value in subscription.dict().items():
        setattr(db_subscription, key, value)
    
    db.commit()
    db.refresh(db_subscription)
    return db_subscription

@app.delete("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
def delete_subscription(subscription_id: int, db: Session = Depends(get_db)):
    db_subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if db_subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    db_subscription.is_active = False
    # db.delete(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription

@app.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription_by_id(subscription_id: int, db: Session = Depends(get_db)):
    db_subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if db_subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return db_subscription

# magazines = [
#     {"name": "Magazine A", "plans": ["1", "2"], "discounts": {"1": 0.1, "2": 0.2}},
#     {"name": "Magazine B", "plans": ["3", "4"], "discounts": {"3": 0.15, "4": 0.25}},
# ]

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


# @app.post("/subscriptions", response_model=None)
# def create_subscription(magazine_name: str, plan: str, user_id: str, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     subscription = {"magazine_name": magazine_name, "plan": plan}
#     user.subscriptions.append(subscription)
#     db.add(user)  # Ensure the user instance is added to the session
#     db.commit()
#     return {"message": "Subscription created successfully"}

# @app.get("/subscriptions", response_model=None)
# def get_subscriptions(user_id: str, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     return user.subscriptions

# @app.get("/subscriptions/{subscription_id}", response_model=None)
# def get_subscription(subscription_id: str, db: Session = Depends(get_db)):
#     subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
#     if not subscription:
#         raise HTTPException(status_code=404, detail="Subscription not found")
    
#     return subscription

# @app.delete("/subscriptions/{subscription_id}", response_model=None)
# def cancel_subscription(subscription_id: str, db: Session = Depends(get_db)):
#     subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
#     if not subscription:
#         raise HTTPException(status_code=404, detail="Subscription not found")
    
#     db.delete(subscription)
#     db.commit()
#     return {"message": "Subscription cancelled successfully"}