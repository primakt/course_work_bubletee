from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from base import get_db
from models.order import Order
from models.user import User
from utils.auth import get_current_user
import pandas as pd
import json
from io import StringIO, BytesIO

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/orders")
def export_orders(
    format: str = "json",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    orders = db.query(Order).all()

    data = []
    for order in orders:
        data.append({
            "id": order.id,
            "user_id": order.user_id,
            "status": order.status,
            "total_price": str(order.total_price),
            "pickup_time": order.pickup_time.isoformat(),
            "created_at": order.created_at.isoformat()
        })

    if format == "json":
        return StreamingResponse(
            iter([json.dumps(data, ensure_ascii=False, indent=2)]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=orders.json"}
        )

    elif format == "csv":
        df = pd.DataFrame(data)
        stream = StringIO()
        df.to_csv(stream, index=False)
        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=orders.csv"
        return response

    else:
        raise HTTPException(status_code=400, detail="Формат должен быть json или csv")