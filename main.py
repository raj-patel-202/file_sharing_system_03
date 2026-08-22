import os

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api import auth, files, permissions, uploads
from core.database import engine
from frontend import routes as frontend_routes
from models.base import Base

app = FastAPI(title="File Sharing System")

os.makedirs("storage/uploads", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(files.router)
app.include_router(permissions.router)
app.include_router(uploads.router)
app.include_router(frontend_routes.router)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
