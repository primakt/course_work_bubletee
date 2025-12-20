from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from base import get_db
from models.newsletter import Newsletter
from models.user_subscription import UserSubscription
from models.user import User
from schemas.newsletter import NewsletterCreate
from utils.auth import get_current_user

router = APIRouter(prefix="/newsletter", tags=["newsletter"])

def fake_send_to_telegram(user: User, title: str, message: str):
    print(f"[SIMULATION] Отправка сообщения пользователю {user.telegram_id} ({user.username or user.first_name}):")
    print(f"Заголовок: {title}")
    print(f"Текст: {message}\n")

@router.post("/send", status_code=status.HTTP_202_ACCEPTED)
def send_broadcast(
    newsletter: NewsletterCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    subscribed_users = db.query(User).join(UserSubscription).filter(UserSubscription.subscribed == True).all()

    if not subscribed_users:
        raise HTTPException(status_code=400, detail="Нет подписанных пользователей")

    db_newsletter = Newsletter(
        title=newsletter.title,
        message=newsletter.message,
        sent_by=current_user.id
    )
    db.add(db_newsletter)
    db.commit()

    for user in subscribed_users:
        background_tasks.add_task(fake_send_to_telegram, user, newsletter.title, newsletter.message)

    return {"detail": f"Рассылка запущена для {len(subscribed_users)} пользователей (симуляция)"}

@router.get("/subscriptions")
def get_subscription_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    subscription = db.query(UserSubscription).filter(UserSubscription.user_id == current_user.id).first()
    return {"subscribed": subscription.subscribed if subscription else True}