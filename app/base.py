from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from config import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base = declarative_base()