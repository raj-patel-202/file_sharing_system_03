import os

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

from api import auth, files, permissions, uploads
from core.database import engine
from frontend import routes as frontend_routes
from models.base import Base

app = FastAPI(title="File Sharing System")

os.makedirs("storage/uploads", exist_ok=True)


class CacheAndSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add cache-control headers for static assets and security headers for all responses."""

    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)
        path = request.url.path

        # Cache static assets for 1 year (immutable)
        if path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


app.add_middleware(CacheAndSecurityHeadersMiddleware)

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
