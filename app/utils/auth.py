from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from models.user import User
from models.role import Role
from base import get_db
import hashlib
import hmac
import time
import json
from urllib.parse import unquote

BOT_TOKEN = "8570082511:AAHG7sH59V95DdGG95_Tb9IJneJup1xbqfE"

def verify_telegram_init_data(init_data: str) -> dict:
    try:
        parsed = {}
        for pair in init_data.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                parsed[key] = unquote(value)
        
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            raise HTTPException(status_code=401, detail="Hash not found in init data")
        
        data_check_pairs = [f"{k}={v}" for k, v in sorted(parsed.items())]
        data_check_string = "\n".join(data_check_pairs)
        
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=BOT_TOKEN.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != received_hash:
            raise HTTPException(status_code=401, detail="Invalid Telegram data signature")
        
        auth_date = int(parsed.get("auth_date", 0))
        if time.time() - auth_date > 86400:
            raise HTTPException(status_code=401, detail="Telegram data expired")
        
        user_json = parsed.get("user")
        if not user_json:
            raise HTTPException(status_code=401, detail="User data not found")
        
        user_data = json.loads(user_json)
        return user_data
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=401, detail="Invalid user data format")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Auth error: {str(e)}")


async def get_current_user(
    x_telegram_init_data: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    if not x_telegram_init_data:
        raise HTTPException(
            status_code=401,
            detail="Telegram init data required"
        )
    
    user_data = verify_telegram_init_data(x_telegram_init_data)
    telegram_id = user_data["id"]
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        customer_role = db.query(Role).filter(Role.name == "customer").first()
        if not customer_role:
            customer_role = Role(name="customer")
            db.add(customer_role)
            db.flush()
        
        user = User(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            role_id=customer_role.id,
            points=0
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    if not current_user.role:
        current_user.role = db.query(Role).filter(Role.id == current_user.role_id).first()
    
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    return current_user