from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.menu import router as menu_router
from routers.promotion import router as promotion_router
from routers.order import router as order_router
import uvicorn

app = FastAPI(title="Teezy Loyalty System", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(menu_router)
app.include_router(promotion_router)
app.include_router(order_router)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)