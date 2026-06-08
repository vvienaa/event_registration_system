from fastapi import FastAPI, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import desc
import os
from dotenv import load_dotenv

from app.database import SessionLocal, engine
from app.models import Base, Team
from app.qr_utils import generate_qr_code
from app.email_utils import send_qr_email      # ← ДЛЯ ОТПРАВКИ ПИСЕМ
from app.excel_utils import export_to_excel
from PIL import Image
from pyzbar.pyzbar import decode
import io
import re

load_dotenv()

app = FastAPI(title="Event Registration System")

os.makedirs("app/static/qr_codes", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def check_admin(request: Request):
    return request.cookies.get("admin_logged") == "true"


@app.get("/", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", context={"request": request})


@app.post("/register")
async def register_team(
    request: Request,
    team_name: str = Form(...),
    captain_name: str = Form(...),
    captain_email: str = Form(...),
    participant_count: int = Form(...),
    institution: str = Form(None),
    db: Session = Depends(get_db)
):
    # Проверка на дубликат названия команды
    existing = db.query(Team).filter(Team.team_name == team_name).first()
    if existing:
        return templates.TemplateResponse("register.html", context={
            "request": request,
            "error": "Команда с таким названием уже зарегистрирована"
        })
    
    # Создание новой команды
    new_team = Team(
        team_name=team_name,
        captain_name=captain_name,
        captain_email=captain_email,
        participant_count=participant_count,
        institution=institution
    )
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    
    # Генерация QR-кода
    qr_path = generate_qr_code(new_team.id, team_name, captain_email)
    new_team.qr_code_path = qr_path
    db.commit()
    
    # ✅ ОТПРАВКА QR-КОДА НА ПОЧТУ КАПИТАНА
    send_qr_email(captain_email, team_name, qr_path)
    
    return templates.TemplateResponse("success.html", context={
        "request": request,
        "team_name": team_name,
        "email": captain_email,
        "team_id": new_team.id
    })


@app.get("/download-qr/{team_id}")
async def download_qr(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team or not team.qr_code_path:
        raise HTTPException(status_code=404, detail="QR-код не найден")
    if not os.path.exists(team.qr_code_path):
        raise HTTPException(status_code=404, detail="Файл QR-кода не найден")
    return FileResponse(
        path=team.qr_code_path,
        filename=f"qr_code_{team.team_name.replace(' ', '_')}.png",
        media_type="image/png"
    )


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_form(request: Request):
    return templates.TemplateResponse("admin_login.html", context={"request": request})


@app.post("/admin/login")
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(key="admin_logged", value="true", httponly=True)
        return response
    return templates.TemplateResponse("admin_login.html", context={
        "request": request,
        "error": "Неверный логин или пароль"
    })


@app.get("/admin/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("admin_logged")
    return response


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    if not check_admin(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    teams = db.query(Team).order_by(desc(Team.created_at)).all()
    total_participants = sum(t.participant_count for t in teams)
    return templates.TemplateResponse("admin.html", context={
        "request": request,
        "teams": teams,
        "total_teams": len(teams),
        "total_participants": total_participants
    })


@app.get("/export/excel")
async def export_excel_endpoint(request: Request, db: Session = Depends(get_db)):
    if not check_admin(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    teams = db.query(Team).all()
    excel_data = export_to_excel(teams)
    return StreamingResponse(
        io.BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=teams_report.xlsx"}
    )


@app.get("/scan", response_class=HTMLResponse)
async def scan_page(request: Request):
    return templates.TemplateResponse("scan.html", context={"request": request})


@app.post("/verify-qr")
async def verify_qr(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        decoded_objects = decode(img)
        if not decoded_objects:
            return {"status": "error", "message": "QR-код не распознан"}
        qr_data = decoded_objects[0].data.decode()
        match = re.search(r"TEAM_ID:(\d+)", qr_data)
        if not match:
            return {"status": "error", "message": "Неверный формат QR-кода"}
        team_id = int(match.group(1))
        team = db.query(Team).filter(Team.id == team_id).first()
        if team:
            return {
                "status": "success",
                "message": "ДОПУЩЕН",
                "team_name": team.team_name,
                "captain_name": team.captain_name,
                "participant_count": team.participant_count
            }
        else:
            return {"status": "error", "message": "Команда не найдена"}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка: {str(e)}"}