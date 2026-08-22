from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from utils.security import get_current_user_id

router = APIRouter(tags=["frontend"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user_id = get_current_user_id(request)
    if user_id:
        return templates.TemplateResponse("files.html", {"request": request, "user_id": user_id})
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/files", response_class=HTMLResponse)
async def files_page(request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("files.html", {"request": request, "user_id": user_id})

@router.get("/my-uploads", response_class=HTMLResponse)
async def my_uploads_page(request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("my_uploads.html", {"request": request, "user_id": user_id})

@router.get("/requests", response_class=HTMLResponse)
async def requests_page(request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("requests.html", {"request": request, "user_id": user_id})

@router.get("/files/{file_id}", response_class=HTMLResponse)
async def file_detail_page(file_id: int, request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("file_detail.html", {"request": request, "file_id": file_id, "user_id": user_id})

@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("upload.html", {"request": request})
