from pydantic import BaseModel

class NewsletterCreate(BaseModel):
    title: str
    message: str