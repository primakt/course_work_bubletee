from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from models.user import User
from base import get_db
import hashlib
import hmac
import time
import json

bearer_scheme = HTTPBearer()

BOT_TOKEN = "8570082511:AAHG7sH59V95DdGG95_Tb9IJneJup1xbqfE"

def verify_telegram_init_data(init_data: str) -> dict:
    data_check_string = []
    parsed_data = {}
    for key, value in [pair.split("=", 1) for pair in init_data.split("&")]:
        parsed_data[key] = value
        if key != "hash":
            data_check_string.append(f"{key}={value}")
    
    data_check_string = "\n".join(sorted(data_check_string))
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if calculated_hash != parsed_data.get("hash"):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    auth_date = int(parsed_data.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        raise HTTPException(status_code=401, detail="Telegram data expired")
    
    user_data = json.loads(parsed_data["user"])
    return user_data

def get_current_user(telegram_init_data: str, db: Session = Depends(get_db)):
    user_data = verify_telegram_init_data(telegram_init_data)
    telegram_id = user_data["id"]
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            role="customer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user