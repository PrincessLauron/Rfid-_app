from fastapi import FastAPI, Request, Form, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .routers import auth as auth_router
from .routers import assets as assets_router
from .routers import logs as logs_router
from .routers import ingest as ingest_router
from .routers import views as views_router
from .routers import tags as tags_router
from .routers import inventory as inventory_router
from .routers import schedule as schedule_router

from .db import get_db
from . import models

from .db import engine, Base
# This line forces SQLAlchemy to look at your models and create missing tables automatically
Base.metadata.create_all(bind=engine)

# ===========================================================================
# 1. INITIALIZE APP (ONLY ONCE)
# ===========================================================================
app = FastAPI(title="Lab Asset Management API")


@app.on_event("startup")
async def clear_schedule_data():
    """Clear all sample schedule data and bookings on startup"""
    try:
        # Clear schedule router data
        from .routers import schedule as schedule_router
        # Log which module file was imported for troubleshooting
        try:
            print(f"Schedule router module: {getattr(schedule_router, '__file__', 'unknown')}")
        except Exception:
            pass
        if hasattr(schedule_router, 'SCHEDULE_DATA'):
            # Log counts before clearing
            try:
                counts = {lab: sum(len(v) for v in lab_sched.values()) for lab, lab_sched in schedule_router.SCHEDULE_DATA.items()}
                print(f"Schedule entries before clear: {counts}")
            except Exception:
                pass
            for lab_name in list(schedule_router.SCHEDULE_DATA.keys()):
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                for day in days:
                    schedule_router.SCHEDULE_DATA[lab_name][day] = {}
        if hasattr(schedule_router, 'bookings'):
            schedule_router.bookings.clear()
        print("✓ Schedule data cleared on startup")
    except Exception as e:
        print(f"⚠ Error clearing schedule data: {e}")


# ===========================================================================
# 2. EXCEPTION HANDLER
# ===========================================================================
_STATUS_LABELS = {
    400: "Missing or Invalid Information",
    403: "Access Denied",
    404: "Not Found",
    409: "Already Exists",
    422: "Validation Error",
    500: "Something Went Wrong",
}

_FRIENDLY_MESSAGES = {
    "Reference number and issued date are required": "Please fill in the Reference Number and Issue Date fields.",
    "Select an assignee or add a new one": "Please select a recipient or enter a new recipient name.",
    "Reference number already exists": "This Reference Number is already in use. Please choose a different one.",
    "Incorrect admin password": "The admin password you entered is incorrect. Please try again.",
    "Admin access required": "This action requires administrator access.",
    "Insufficient permissions": "You do not have permission to perform this action.",
    "Room not found": "The requested laboratory could not be found.",
    "Asset not found": "The requested asset could not be found.",
    "MR not found": "The requested Memorandum Receipt could not be found.",
}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    accept = request.headers.get("accept", "")
    xhr = request.headers.get("x-requested-with", "").lower() == "xmlhttprequest"
    hx = request.headers.get("hx-request", "")

    if xhr or hx:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    if "text/html" in accept:
        label = _STATUS_LABELS.get(exc.status_code, f"Error {exc.status_code}")
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        detail = _FRIENDLY_MESSAGES.get(detail, detail)
        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{label} — CCS LAMS</title>
  <link rel="stylesheet" href="/static/styles.css">
  <style>
    body {{ margin:0; background: var(--c7, #F3F6F8); }}
    .error-page {{ display:flex; align-items:center; justify-content:center; min-height:100vh; }}
  </style>
</head>
<body>
  <div class="error-page">
    <div class="modal-overlay" style="display:flex; position:relative; background:transparent;">
      <div class="modal-box" style="max-width:440px;">
        <div class="error-modal-icon">
          <svg viewBox="0 0 24 24" width="48" height="48"><path fill="#E74C3C" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
        </div>
        <h3>{label}</h3>
        <p style="word-break:break-word;">{detail}</p>
        <div class="modal-actions">
          <button type="button" class="btn-cancel" onclick="history.back()">Go Back</button>
        </div>
      </div>
    </div>
  </div>
</body>
</html>"""
        return HTMLResponse(content=html, status_code=exc.status_code)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# ===========================================================================
# 3. ROUTES (Must go BEFORE routers)
# ===========================================================================
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/create-laboratory")
async def redirect_typing_mistake():
    return RedirectResponse(url="/dashboard")


@app.post("/create-laboratory")
async def create_room(
    room_name: str = Form(...),
    db: Session = Depends(get_db),
):
    name = room_name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Laboratory name cannot be empty.")
    existing = db.query(models.Room).filter(models.Room.name == name).first()
    if existing:
        raise HTTPException(status_code=409, detail="A laboratory with that name already exists.")
    new_room = models.Room(name=name)
    db.add(new_room)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/rooms/delete/{room_id}")
async def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
):
    room = db.get(models.Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    db.delete(room)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)


# ===========================================================================
# 4. EXTERNAL ROUTERS
# ===========================================================================
app.include_router(auth_router.router)
app.include_router(views_router.router)
app.include_router(assets_router.router)
app.include_router(logs_router.router)
app.include_router(ingest_router.router)
app.include_router(tags_router.router)
app.include_router(inventory_router.router)
app.include_router(schedule_router.router)


# ===========================================================================
# 5. MOUNT STATIC FILES
# ===========================================================================
app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")