from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.menu import router as menu_router
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

@app.get("/")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)