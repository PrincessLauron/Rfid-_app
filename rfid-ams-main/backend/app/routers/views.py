from datetime import datetime, timezone
import csv
import io
import re
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError


from ..db import get_db
from .. import models
from ..security import verify_password, create_access_token, create_refresh_token
from ..sessions import set_tokens_in_cookies, clear_tokens, get_access_from_cookies
from ..deps import current_user_from_cookie


templates = Jinja2Templates(directory="backend/app/templates")
router = APIRouter(tags=["views"])




def _component_code(component_type: str | None) -> str:
    mapping = {
        "pc": "PC",
        "keyboard": "KB",
        "mouse": "MS",
        "monitor": "MN",
        "cables": "CB",
        "cable": "CB",
    }
    if not component_type:
        return "AS"
    return mapping.get(component_type.lower(), component_type[:2].upper())




def _room_code(room: models.Room | None) -> str:
    if not room:
        return "GEN"
    if room.code:
        return room.code.upper().replace(" ", "")
    parts = [w[0].upper() for w in room.name.split() if w]
    return "".join(parts[:4]) or "LAB"




def _public_asset_id(asset: models.Asset) -> str:
    return f"LAB-{_room_code(asset.room)}-{_component_code(asset.component_type)}-{asset.id:04d}"




def _asset_category(asset: models.Asset) -> str:
    text = f"{asset.name or ''} {asset.component_type or ''}".lower()
    if any(k in text for k in ["all-in-one", "imac", "aio"]):
        return "All-in-One PC"
    if any(k in text for k in ["desktop", "pc", "computer"]):
        return "Desktop PC"
    if "monitor" in text or (asset.component_type or "").lower() == "monitor":
        return "Monitor"
    if "keyboard" in text or (asset.component_type or "").lower() == "keyboard":
        return "Keyboard"
    if "mouse" in text or (asset.component_type or "").lower() == "mouse":
        return "Mouse"
    if any(k in text for k in ["cable", "hdmi", "ethernet", "vga"]):
        return "Cable"
    if "adapter" in text:
        return "Adapter"
    if "projector" in text:
        return "Projector"
    if "tv" in text:
        return "TV/Display"
    if any(k in text for k in ["air conditioner", "aircon", "ac unit", " a/c "]):
        return "Air Conditioner"
    return "Other Asset"




def _build_inferred_bundles(assets: list[models.Asset]) -> list[dict[str, str | None]]:
    primaries = [
        a for a in assets if _asset_category(a) in {"All-in-One PC", "Desktop PC", "Laptop"}
    ]
    primaries.sort(key=lambda a: a.id)


    def bucket(cat: str) -> list[models.Asset]:
        items = [a for a in assets if _asset_category(a) == cat]
        items.sort(key=lambda a: a.id)
        return items


    mice = bucket("Mouse")
    keyboards = bucket("Keyboard")
    adapters = bucket("Adapter")
    cables = bucket("Cable")
    monitors = bucket("Monitor")


    bundles: list[dict[str, str | None]] = []
    for i, parent in enumerate(primaries):
        bundles.append(
            {
                "unit_id": _public_asset_id(parent),
                "unit_name": parent.name,
                "unit_category": _asset_category(parent),
                "mouse": _public_asset_id(mice[i]) if i < len(mice) else None,
                "keyboard": _public_asset_id(keyboards[i]) if i < len(keyboards) else None,
                "adapter": _public_asset_id(adapters[i]) if i < len(adapters) else None,
                "cable": _public_asset_id(cables[i]) if i < len(cables) else None,
                "monitor": _public_asset_id(monitors[i]) if i < len(monitors) else None,
            }
        )
    return bundles




def _asset_tag_status(asset: models.Asset) -> str:
    if asset.tag_epc:
        return "Tagged"
    for tag in asset.registered_tags:
        if tag.status == "active":
            return "Tagged"
    return "No tag yet"




def _asset_mr_label(asset: models.Asset) -> str:
    try:
        active = [mr for mr in asset.memorandum_receipts if mr.status == "active"]
    except OperationalError:
        return "MR: Unassigned"
    if not active:
        return "MR: Unassigned"
    active.sort(key=lambda x: x.issued_at or datetime.min, reverse=True)
    latest = active[0]
    assignee = latest.assignee.name if latest.assignee else latest.issued_to
    return f"MR: {assignee}"




def _extract_unit_key(asset_name: str | None) -> str | None:
    """
    Extract identifiers like ML.1, DB.10, CS.5, or trailing numbers used in current inventory labels.
    """
    if not asset_name:
        return None
    text = asset_name.strip()
    m = re.search(r"([A-Z]{1,4}\.\d+)$", text)
    if m:
        return m.group(1)
    m = re.search(r"(\d+)$", text)
    if m:
        return m.group(1)
    return None




def _is_aio_pc(asset: models.Asset) -> bool:
    return _asset_category(asset) == "All-in-One PC"




def _unit_sort_tuple(asset: models.Asset) -> tuple[str, int, str]:
    room_code = _room_code(asset.room)
    key = _extract_unit_key(asset.name) or ""
    m = re.search(r"(\d+)$", key)
    num = int(m.group(1)) if m else 0
    return (room_code, num, (asset.name or "").lower())




def _display_room_name(name: str) -> str:
    mapping = {
        "CS Lab": "CS Laboratory",
        "Database Lab": "Database Laboratory",
    }
    return mapping.get(name, name)




def _format_relative(ts: datetime | None) -> str:
    if not ts:
        return "No scans yet"
    now = datetime.now(timezone.utc)
    point = ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)
    mins = int((now - point).total_seconds() // 60)
    if mins < 1:
        return "Scanned just now"
    if mins < 60:
        return f"Scanned {mins} min ago"
    hours = mins // 60
    if hours < 24:
        return f"Scanned {hours} hour(s) ago"
    return f"Scanned {hours // 24} day(s) ago"




def _breadcrumbs(*items: tuple[str, str | None]) -> list[dict[str, str | None]]:
    return [{"label": label, "href": href} for label, href in items]




@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    access_cookie = get_access_from_cookies(request)
    if access_cookie:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)




@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db), user: models.User = Depends(current_user_from_cookie)):
    total_assets = db.query(models.Asset).count()
    active_anomaly_count = (
        db.query(models.Anomaly).filter(models.Anomaly.status != "resolved").count()
    )


    rooms = db.query(models.Room).order_by(models.Room.name.asc()).all()
    room_cards = []
    for room in rooms:
        asset_count = db.query(models.Asset).filter(models.Asset.room_id == room.id).count()
        pc_count = (
            db.query(models.Asset)
            .filter(models.Asset.room_id == room.id, models.Asset.component_type == "pc")
            .count()
        )
        anomaly_count = db.query(models.Anomaly).filter(
            models.Anomaly.room_id == room.id, models.Anomaly.status != "resolved"
        ).count()
        last_scan = (
            db.query(models.ScanSession)
            .filter(models.ScanSession.room_id == room.id, models.ScanSession.status == "closed")
            .order_by(models.ScanSession.ended_at.desc())
            .first()
        )
        room_cards.append(
            {
                "room": room,
                "room_display_name": _display_room_name(room.name),
                "asset_count": asset_count,
                "pc_count": pc_count,
                "anomaly_count": anomaly_count,
                "scan_freshness": _format_relative(last_scan.ended_at if last_scan else None),
            }
        )


    # Build notifications panel data
    _ANOMALY_TYPE_LABELS = {
        "missing": ("Missing Asset", "red"),
        "transfer": ("Unexpected Transfer", "amber"),
        "incomplete_group": ("Incomplete Unit", "amber"),
    }
    recent_anomalies = (
        db.query(models.Anomaly)
        .filter(models.Anomaly.status != "resolved")
        .order_by(models.Anomaly.first_seen_at.desc())
        .limit(8)
        .all()
    )
    notification_items = []
    for anomaly in recent_anomalies:
        room_obj = db.get(models.Room, anomaly.room_id) if anomaly.room_id else None
        asset_obj = db.get(models.Asset, anomaly.asset_id) if anomaly.asset_id else None
        room_name = _display_room_name(room_obj.name) if room_obj else "Unknown Lab"
        asset_name = asset_obj.name if asset_obj else "Unknown Asset"
        type_label, color = _ANOMALY_TYPE_LABELS.get(
            anomaly.type, (anomaly.type.replace("_", " ").title(), "amber")
        )
        notification_items.append({
            "type": anomaly.type,
            "type_label": type_label,
            "color": color,
            "room_name": room_name,
            "room_id": anomaly.room_id,
            "asset_name": asset_name,
            "time_ago": _format_relative(anomaly.first_seen_at),
        })


    scan_activity = [
        {
            "room_name": r["room_display_name"],
            "room_id": r["room"].id,
            "scan_freshness": r["scan_freshness"],
            "anomaly_count": r["anomaly_count"],
        }
        for r in room_cards
    ]


    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Dashboard",
            "user": user,
            "breadcrumbs": _breadcrumbs(("Dashboard", None)),
            "total_assets": total_assets,
            "total_rooms": len(rooms),
            "active_anomaly_count": active_anomaly_count,
            "room_cards": room_cards,
            "notification_items": notification_items,
            "scan_activity": scan_activity,
        },
    )


def _component_type_label(component_type: str | None, asset_name: str | None = None) -> str:
    """Human-readable label for component_type values.
    When asset_name is provided for a PC, detect AIO vs Desktop."""
    labels = {
        "monitor": "Monitor",
        "mouse": "Mouse",
        "keyboard": "Keyboard",
        "adapter": "Adapter",
        "cables": "Ethernet Cable",
        "cable": "Ethernet Cable",
    }
    if not component_type:
        return "Other"
    ct = component_type.lower()
    if ct == "pc":
        name_lower = (asset_name or "").lower()
        if any(kw in name_lower for kw in ["imac", "aio", "all-in-one", "vivo"]):
            return "AIO PC"
        return "Desktop PC"
    return labels.get(ct, component_type.title())




def _status_display(status: str | None) -> str:
    """Human-readable status label from DB value."""
    mapping = {
        "in_service": "In Service",
        "condemned": "Condemned",
        "transferred": "Transferred",
        "maintenance": "For Maintenance",
    }
    if not status:
        return "Unknown"
    return mapping.get(status.lower(), status.replace("_", " ").title())




def _location_sort_key(location: str) -> tuple[str, int]:
    """Sort locations naturally: extract trailing number for numeric sort."""
    m = re.search(r"(\d+)$", location)
    num = int(m.group(1)) if m else 0
    prefix = re.sub(r"\d+$", "", location).strip()
    return (prefix.lower(), num)




@router.get("/rooms/{room_id}", response_class=HTMLResponse)
def room_detail(
    room_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    room = db.get(models.Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")


    all_assets = (
        db.query(models.Asset)
        .filter(models.Asset.room_id == room.id)
        .order_by(models.Asset.id.asc())
        .all()
    )
    anomaly_count = (
        db.query(models.Anomaly)
        .filter(models.Anomaly.room_id == room.id, models.Anomaly.status != "resolved")
        .count()
    )


    # Get open anomaly asset IDs for per-unit indicators
    open_anomalies = (
        db.query(models.Anomaly)
        .filter(models.Anomaly.room_id == room.id, models.Anomaly.status != "resolved")
        .all()
    )
    anomalous_asset_ids = {a.asset_id for a in open_anomalies if a.asset_id}


    # Group assets by location to form PC units
    units_by_location: dict[str, dict] = {}
    for asset in all_assets:
        loc = (asset.location or "Unassigned").strip()
        if loc not in units_by_location:
            units_by_location[loc] = {"pc": None, "components": [], "all_assets": []}
        units_by_location[loc]["all_assets"].append(asset)
        if asset.component_type and asset.component_type.lower() == "pc":
            units_by_location[loc]["pc"] = asset
        else:
            units_by_location[loc]["components"].append(asset)


    # Build cards for each PC unit
    unit_cards = []
    for loc, group in sorted(units_by_location.items(), key=lambda x: _location_sort_key(x[0])):
        pc = group["pc"]
        if not pc:
            continue  # skip orphan peripherals with no PC
        total_components = len(group["all_assets"])
        loc_asset_ids = {a.id for a in group["all_assets"]}
        unit_anomaly_count = len(loc_asset_ids & anomalous_asset_ids)
        unit_cards.append(
            {
                "asset_id": pc.id,
                "location": loc,
                "pc_name": pc.name,
                "status": pc.status or "unknown",
                "status_display": _status_display(pc.status),
                "total_components": total_components,
                "mr_label": _asset_mr_label(pc),
                "tag_status": _asset_tag_status(pc),
                "has_anomaly": unit_anomaly_count > 0,
                "unit_anomaly_count": unit_anomaly_count,
            }
        )


    pc_count = len(unit_cards)
    untagged_count = sum(1 for a in all_assets if _asset_tag_status(a) == "No tag yet")


    user_roles = {r.name for r in user.roles}
    can_edit = bool({"admin", "technician"} & user_roles)
    is_admin = "admin" in user_roles


    return templates.TemplateResponse(
        "room_detail.html",
        {
            "request": request,
            "title": _display_room_name(room.name),
            "user": user,
            "breadcrumbs": _breadcrumbs(("Dashboard", "/dashboard"), (_display_room_name(room.name), None)),
            "room": room,
            "room_display_name": _display_room_name(room.name),
            "total_assets": len(all_assets),
            "pc_count": pc_count,
            "anomaly_count": anomaly_count,
            "untagged_count": untagged_count,
            "unit_cards": unit_cards,
            "status_options": ASSET_STATUS_OPTIONS,
            "can_edit": can_edit,
            "is_admin": is_admin,
        },
    )




@router.get("/rooms/{room_id}/units/{asset_id}", response_class=HTMLResponse)
def room_unit_detail(
    room_id: int,
    asset_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    room = db.get(models.Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    main_asset = db.get(models.Asset, asset_id)
    if not main_asset or main_asset.room_id != room.id:
        raise HTTPException(status_code=404, detail="Unit not found in this room")


    # Find ALL assets at this location (the full PC bundle)
    location = (main_asset.location or "").strip()
    if location:
        all_unit_assets = (
            db.query(models.Asset)
            .filter(
                models.Asset.room_id == room.id,
                models.Asset.location == location,
            )
            .order_by(models.Asset.id.asc())
            .all()
        )
    else:
        all_unit_assets = [main_asset]


    # Separate PC (main) from peripherals, build rich rows for ALL components
    component_order = {"pc": 0, "monitor": 1, "keyboard": 2, "mouse": 3, "adapter": 4, "cables": 5, "cable": 5}
    all_unit_assets.sort(key=lambda a: component_order.get((a.component_type or "").lower(), 99))


    component_rows = []
    for a in all_unit_assets:
        component_rows.append(
            {
                "id": a.id,
                "public_id": _public_asset_id(a),
                "name": a.name,
                "type_label": _component_type_label(a.component_type, a.name),
                "component_type": a.component_type or "-",
                "serial_number": a.serial_number or "-",
                "status": a.status or "-",
                "specs": a.specs or "-",
                "tag_status": _asset_tag_status(a),
                "mr_label": _asset_mr_label(a),
            }
        )


    user_roles = {r.name for r in user.roles}
    can_edit = bool({"admin", "technician"} & user_roles)
    is_admin = "admin" in user_roles


    return templates.TemplateResponse(
        "room_unit_detail.html",
        {
            "request": request,
            "title": f"{_display_room_name(room.name)} — {location or 'Unit'}",
            "user": user,
            "breadcrumbs": _breadcrumbs(
                ("Dashboard", "/dashboard"),
                (_display_room_name(room.name), f"/rooms/{room.id}"),
                (location or f"Unit #{main_asset.id}", None),
            ),
            "room": room,
            "room_display_name": _display_room_name(room.name),
            "location": location or "Unassigned",
            "pc_name": main_asset.name,
            "pc_public_id": _public_asset_id(main_asset),
            "pc_status": _status_display(main_asset.status),
            "pc_mr_label": _asset_mr_label(main_asset),
            "pc_tag_status": _asset_tag_status(main_asset),
            "pc_specs": main_asset.specs or "-",
            "total_components": len(all_unit_assets),
            "component_rows": component_rows,
            "status_options": ASSET_STATUS_OPTIONS,
            "component_type_choices": COMPONENT_TYPE_CHOICES,
            "can_edit": can_edit,
            "is_admin": is_admin,
            "main_asset_id": main_asset.id,
        },
    )




ASSET_STATUS_OPTIONS = [
    ("in_service", "In Service"),
    ("condemned", "Condemned"),
    ("transferred", "Transferred"),
    ("maintenance", "For Maintenance"),
]




@router.post("/rooms/{room_id}/units/{asset_id}/components/{component_id}/update-status")
def update_component_status(
    room_id: int,
    asset_id: int,
    component_id: int,
    new_status: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    """Inline status update for a single component within a PC unit."""
    role_names = {r.name for r in user.roles}
    if not ({"admin", "technician"} & role_names):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


    valid_statuses = {code for code, _ in ASSET_STATUS_OPTIONS}
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")


    asset = db.get(models.Asset, component_id)
    if not asset or asset.room_id != room_id:
        raise HTTPException(status_code=404, detail="Component not found in this room")


    old_status = asset.status
    asset.status = new_status
    db.add(
        models.ActivityLog(
            action="asset_status_change",
            user_id=user.id,
            asset_id=asset.id,
            details=f"Status changed from '{old_status}' to '{new_status}'",
        )
    )
    db.commit()
    return RedirectResponse(
        url=f"/rooms/{room_id}/units/{asset_id}", status_code=302
    )




@router.post("/rooms/{room_id}/units/{asset_id}/components/{component_id}/delete")
def delete_component(
    room_id: int,
    asset_id: int,
    component_id: int,
    admin_password: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    """Delete a component from a PC unit. Requires admin password confirmation."""
    # Must be admin
    if "admin" not in {r.name for r in user.roles}:
        raise HTTPException(status_code=403, detail="Admin access required")


    # Verify admin password
    if not verify_password(admin_password, user.password_hash):
        raise HTTPException(status_code=403, detail="Incorrect admin password")


    asset = db.get(models.Asset, component_id)
    if not asset or asset.room_id != room_id:
        raise HTTPException(status_code=404, detail="Component not found in this room")


    asset_name = asset.name
    asset_public_id = _public_asset_id(asset)


    db.add(
        models.ActivityLog(
            action="asset_delete",
            user_id=user.id,
            details=f"Deleted asset '{asset_name}' ({asset_public_id}) from room {room_id}",
        )
    )
    db.delete(asset)
    db.commit()


    # If the deleted asset was the main PC (the one in the URL), redirect to room
    if component_id == asset_id:
        return RedirectResponse(url=f"/rooms/{room_id}", status_code=302)


    return RedirectResponse(
        url=f"/rooms/{room_id}/units/{asset_id}", status_code=302
    )




COMPONENT_TYPE_CHOICES = [
    ("monitor", "Monitor"),
    ("keyboard", "Keyboard"),
    ("mouse", "Mouse"),
    ("adapter", "Adapter"),
    ("cables", "Ethernet Cable"),
]




@router.post("/rooms/{room_id}/units/{asset_id}/add-component")
def add_component(
    room_id: int,
    asset_id: int,
    comp_type: str = Form(...),
    comp_name: str = Form(...),
    comp_serial: str = Form(""),
    comp_status: str = Form("in_service"),
    comp_specs: str = Form(""),
    request: Request = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    """Add a new peripheral component to a PC unit."""
    role_names = {r.name for r in user.roles}
    if not ({"admin", "technician"} & role_names):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


    valid_types = {code for code, _ in COMPONENT_TYPE_CHOICES}
    if comp_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid component type: {comp_type}")


    valid_statuses = {code for code, _ in ASSET_STATUS_OPTIONS}
    if comp_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status: {comp_status}")


    main_asset = db.get(models.Asset, asset_id)
    if not main_asset or main_asset.room_id != room_id:
        raise HTTPException(status_code=404, detail="PC unit not found in this room")


    new_asset = models.Asset(
        name=comp_name.strip(),
        component_type=comp_type,
        serial_number=comp_serial.strip() or None,
        status=comp_status,
        specs=comp_specs.strip() or None,
        room_id=room_id,
        location=main_asset.location,
    )
    db.add(new_asset)
    db.flush()


    db.add(
        models.ActivityLog(
            action="asset_create",
            user_id=user.id,
            asset_id=new_asset.id,
            details=f"Added component '{new_asset.name}' ({comp_type}) to unit at {main_asset.location}",
        )
    )
    db.commit()


    return RedirectResponse(url=f"/rooms/{room_id}/units/{asset_id}", status_code=302)




@router.post("/rooms/{room_id}/add-unit")
def add_pc_unit(
    room_id: int,
    unit_name: str = Form(...),
    unit_location: str = Form(...),
    unit_serial: str = Form(""),
    unit_status: str = Form("in_service"),
    unit_specs: str = Form(""),
    request: Request = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    """Add a new PC unit to a laboratory room."""
    role_names = {r.name for r in user.roles}
    if not ({"admin", "technician"} & role_names):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


    valid_statuses = {code for code, _ in ASSET_STATUS_OPTIONS}
    if unit_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status: {unit_status}")


    room = db.get(models.Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")


    if not unit_name.strip() or not unit_location.strip():
        raise HTTPException(status_code=400, detail="Unit name and location are required")


    new_asset = models.Asset(
        name=unit_name.strip(),
        component_type="pc",
        serial_number=unit_serial.strip() or None,
        status=unit_status,
        specs=unit_specs.strip() or None,
        room_id=room_id,
        location=unit_location.strip(),
    )
    db.add(new_asset)
    db.flush()


    db.add(
        models.ActivityLog(
            action="asset_create",
            user_id=user.id,
            asset_id=new_asset.id,
            details=f"Added PC unit '{new_asset.name}' at {new_asset.location} in room {room_id}",
        )
    )
    db.commit()


    return RedirectResponse(url=f"/rooms/{room_id}", status_code=302)




@router.get("/profile", response_class=HTMLResponse)
def profile(request: Request, db: Session = Depends(get_db), user: models.User = Depends(current_user_from_cookie)):
    last_login = (
        db.query(models.ActivityLog)
        .filter(models.ActivityLog.user_id == user.id, models.ActivityLog.action == "login")
        .order_by(models.ActivityLog.created_at.desc())
        .first()
    )
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "title": "Profile",
            "user": user,
            "breadcrumbs": _breadcrumbs(("Dashboard", "/dashboard"), ("Profile", None)),
            "last_login": last_login.created_at if last_login else None,
        },
    )




@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})




@router.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.password_hash) or not user.is_active:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Invalid credentials or inactive user"}, status_code=400
        )
    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    resp = RedirectResponse(url="/dashboard", status_code=302)
    set_tokens_in_cookies(resp, access, refresh)
    return resp




@router.get("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    clear_tokens(resp)
    return resp




@router.get("/ui/assets", response_class=HTMLResponse)
def assets_ui(request: Request, db: Session = Depends(get_db), user: models.User = Depends(current_user_from_cookie)):
    assets = db.query(models.Asset).order_by(models.Asset.created_at.desc()).all()
    rooms = db.query(models.Room).order_by(models.Room.name.asc()).all()
    return templates.TemplateResponse(
        "assets_htmx.html",
        {
            "request": request,
            "title": "Assets",
            "user": user,
            "breadcrumbs": _breadcrumbs(("Dashboard", "/dashboard"), ("Assets", None)),
            "assets": assets,
            "rooms": rooms,
        },
    )




@router.post("/ui/assets/create", response_class=HTMLResponse)
def assets_ui_create(
    request: Request,
    name: str = Form(...),
    serial_number: str | None = Form(None),
    tag_epc: str | None = Form(None),
    location: str | None = Form(None),
    status_: str | None = Form(None, alias="status"),
    component_type: str | None = Form(None),
    room_id: int | None = Form(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    role_names = {r.name for r in user.roles}
    if not ({"admin", "technician"} & role_names):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


    asset = models.Asset(
        name=name,
        serial_number=serial_number or None,
        tag_epc=tag_epc or None,
        location=location or None,
        status=status_ or None,
        component_type=component_type or None,
        room_id=room_id,
    )
    db.add(asset)
    db.flush()
    db.add(models.ActivityLog(action="asset_create", user_id=user.id, asset_id=asset.id))
    db.commit()
    db.refresh(asset)


    return templates.TemplateResponse("partials/asset_row.html", {"request": request, "a": asset})




@router.get("/ui/assets/export.csv")
def export_assets_csv(db: Session = Depends(get_db), user: models.User = Depends(current_user_from_cookie)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["asset_id", "name", "serial_number", "component_type", "status", "location", "room_name"])
    assets = db.query(models.Asset).order_by(models.Asset.id.asc()).all()
    for asset in assets:
        writer.writerow(
            [
                _public_asset_id(asset),
                asset.name,
                asset.serial_number or "",
                asset.component_type or "",
                asset.status or "",
                asset.location or "",
                asset.room.name if asset.room else "",
            ]
        )
    output.seek(0)
    filename = f"ccs_inventory_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )




@router.post("/ui/assets/import.csv")
def import_assets_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    role_names = {r.name for r in user.roles}
    if not ({"admin", "technician"} & role_names):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")


    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    rooms_by_name = {r.name.strip().lower(): r for r in db.query(models.Room).all()}


    created = 0
    for row in reader:
        name = (row.get("name") or "").strip()
        if not name:
            continue
        room_name = (row.get("room_name") or "").strip()
        room = rooms_by_name.get(room_name.lower()) if room_name else None


        asset = models.Asset(
            name=name,
            serial_number=(row.get("serial_number") or "").strip() or None,
            component_type=(row.get("component_type") or "").strip() or None,
            status=(row.get("status") or "").strip() or None,
            location=(row.get("location") or "").strip() or None,
            room_id=room.id if room else None,
        )
        db.add(asset)
        created += 1


    db.add(models.ActivityLog(action="asset_import_csv", user_id=user.id, details=f"Imported {created} assets"))
    db.commit()
    return RedirectResponse(url="/ui/assets", status_code=302)




@router.get("/inventory/assets/{asset_id}/edit-modal", response_class=HTMLResponse)
def edit_asset_modal(
    asset_id: int,
    request: Request,
    next_url: str | None = Query(default=None, alias="next"),
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    """Return just the edit form HTML for embedding inside a modal (no base template)."""
    asset = db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    rooms = db.query(models.Room).order_by(models.Room.name.asc()).all()


    back_url = next_url or request.headers.get("referer", "/inventory")


    return templates.TemplateResponse(
        "_asset_edit_partial.html",
        {
            "request": request,
            "asset": asset,
            "rooms": rooms,
            "status_options": ASSET_STATUS_OPTIONS,
            "component_type_choices": COMPONENT_TYPE_CHOICES,
            "back_url": back_url,
        },
    )




@router.get("/inventory/assets/{asset_id}/edit", response_class=HTMLResponse)
def edit_asset_page(
    asset_id: int,
    request: Request,
    next_url: str | None = Query(default=None, alias="next"),
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    asset = db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    rooms = db.query(models.Room).order_by(models.Room.name.asc()).all()


    # Build a smart back URL: use ?next if provided, otherwise try to build unit URL
    back_url = next_url or "/inventory"
    if not next_url and asset.room_id and asset.location:
        # Find the PC asset at this location to build the unit detail URL
        pc_asset = (
            db.query(models.Asset)
            .filter(
                models.Asset.room_id == asset.room_id,
                models.Asset.location == asset.location,
                models.Asset.component_type == "pc",
            )
            .first()
        )
        if pc_asset:
            back_url = f"/rooms/{asset.room_id}/units/{pc_asset.id}"


    return templates.TemplateResponse(
        "asset_edit.html",
        {
            "request": request,
            "title": f"Edit — {asset.name}",
            "user": user,
            "breadcrumbs": _breadcrumbs(("Dashboard", "/dashboard"), ("Edit Asset", None)),
            "asset": asset,
            "rooms": rooms,
            "status_options": ASSET_STATUS_OPTIONS,
            "back_url": back_url,
        },
    )




@router.post("/inventory/assets/{asset_id}/edit")
async def edit_asset_submit(
    asset_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    role_names = {r.name for r in user.roles}
    if not ({"admin", "technician"} & role_names):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    asset = db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    form = await request.form()
    asset.name = str(form.get("name", asset.name)).strip() or asset.name
    asset.serial_number = str(form.get("serial_number", "")).strip() or None
    asset.component_type = str(form.get("component_type", "")).strip() or None
    asset.status = str(form.get("status", "")).strip() or None
    asset.location = str(form.get("location", "")).strip() or None
    asset.specs = str(form.get("specs", "")).strip() or None
    room_id_raw = str(form.get("room_id", "")).strip()
    asset.room_id = int(room_id_raw) if room_id_raw else None
    db.add(models.ActivityLog(action="asset_edit", user_id=user.id, asset_id=asset.id, details="Edited from UI"))
    db.commit()


    # Redirect back to the unit detail page if possible
    redirect_url = str(form.get("back_url", "/inventory")).strip() or "/inventory"
    return RedirectResponse(url=redirect_url, status_code=302)




@router.post("/inventory/bulk-edit.csv")
def bulk_edit_assets_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    role_names = {r.name for r in user.roles}
    if not ({"admin", "technician"} & role_names):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    updated = 0
    rooms_by_name = {r.name.strip().lower(): r for r in db.query(models.Room).all()}
    for row in reader:
        raw_id = (row.get("asset_db_id") or row.get("asset_id") or "").strip()
        if not raw_id:
            continue
        try:
            asset_id = int(raw_id)
        except ValueError:
            continue
        asset = db.get(models.Asset, asset_id)
        if not asset:
            continue
        if row.get("name"):
            asset.name = row["name"].strip() or asset.name
        if "status" in row:
            asset.status = row["status"].strip() or None
        if "location" in row:
            asset.location = row["location"].strip() or None
        if "component_type" in row:
            asset.component_type = row["component_type"].strip() or None
        if "serial_number" in row:
            asset.serial_number = row["serial_number"].strip() or None
        if "specs" in row:
            asset.specs = row["specs"].strip() or None
        room_name = (row.get("room_name") or "").strip().lower()
        if room_name:
            room = rooms_by_name.get(room_name)
            if room:
                asset.room_id = room.id
        updated += 1
    db.add(models.ActivityLog(action="asset_bulk_edit_csv", user_id=user.id, details=f"Bulk updated {updated} assets"))
    db.commit()
    return RedirectResponse(url="/inventory", status_code=302)




@router.get("/memorandum-receipts", response_class=HTMLResponse)
def memorandum_receipts_view(request: Request, db: Session = Depends(get_db), user: models.User = Depends(current_user_from_cookie)):
    all_mrs = (
        db.query(models.MemorandumReceipt)
        .order_by(models.MemorandumReceipt.issued_at.desc())
        .all()
    )


    user_roles = {r.name for r in user.roles}
    can_edit = bool({"admin", "technician"} & user_roles)
    is_admin = "admin" in user_roles


    mr_rows = []
    for mr in all_mrs:
        mr_rows.append(
            {
                "id": mr.id,
                "reference_no": mr.reference_no,
                "issued_to": mr.assignee.name if mr.assignee else mr.issued_to,
                "issued_by": mr.issued_by or "-",
                "issued_at": mr.issued_at.strftime("%Y-%m-%d") if mr.issued_at else "-",
                "status": mr.status,
                "room_name": mr.room.name if mr.room else "-",
                "asset_count": len(mr.assets),
                "notes": mr.notes or "",
            }
        )


    return templates.TemplateResponse(
        "memorandum_receipts.html",
        {
            "request": request,
            "title": "Memorandum Receipts",
            "user": user,
            "breadcrumbs": _breadcrumbs(("Dashboard", "/dashboard"), ("Memorandum Receipts", None)),
            "mr_rows": mr_rows,
            "total_mrs": len(all_mrs),
            "active_count": sum(1 for m in all_mrs if m.status == "active"),
            "can_edit": can_edit,
            "is_admin": is_admin,
        },
    )




@router.get("/memorandum-receipts/workflow/{asset_id}", response_class=HTMLResponse)
def memorandum_receipt_workflow(
    asset_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    asset = db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")


    assignees = db.query(models.MRAssignee).order_by(models.MRAssignee.name.asc()).all()
    rooms = db.query(models.Room).order_by(models.Room.name.asc()).all()
    all_assets = db.query(models.Asset).order_by(models.Asset.name.asc()).all()


    existing_mr = (
        db.query(models.MemorandumReceipt)
        .join(models.MemorandumReceipt.assets)
        .filter(models.Asset.id == asset_id, models.MemorandumReceipt.status == "active")
        .first()
    )


    return templates.TemplateResponse(
        "memorandum_receipt_workflow.html",
        {
            "request": request,
            "title": "MR Workflow",
            "user": user,
            "breadcrumbs": _breadcrumbs(
                ("Dashboard", "/dashboard"),
                ("Memorandum Receipts", "/memorandum-receipts"),
                (f"Device {asset.id}", None),
            ),
            "asset": asset,
            "public_asset_id": _public_asset_id(asset),
            "assignees": assignees,
            "rooms": rooms,
            "all_assets": all_assets,
            "existing_mr": existing_mr,
        },
    )




@router.post("/memorandum-receipts/workflow/{asset_id}/save")
async def save_memorandum_receipt_workflow(
    asset_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    role_names = {r.name for r in user.roles}
    if not ({"admin", "technician"} & role_names):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


    primary_asset = db.get(models.Asset, asset_id)
    if not primary_asset:
        raise HTTPException(status_code=404, detail="Asset not found")


    form = await request.form()
    reference_no = str(form.get("reference_no", "")).strip()
    issued_by = str(form.get("issued_by", "")).strip() or None
    issued_at_raw = str(form.get("issued_at", "")).strip()
    status = str(form.get("status", "active")).strip() or "active"
    notes = str(form.get("notes", "")).strip() or None
    room_id_raw = str(form.get("room_id", "")).strip()
    existing_mr_id_raw = str(form.get("existing_mr_id", "")).strip()
    assignee_id_raw = str(form.get("assignee_id", "")).strip()
    new_assignee_name = str(form.get("new_assignee_name", "")).strip()
    new_assignee_initials = str(form.get("new_assignee_initials", "")).strip() or None
    asset_ids_raw = form.getlist("asset_ids")


    if not reference_no or not issued_at_raw:
        raise HTTPException(status_code=400, detail="reference_no and issued_at are required")


    try:
        issued_at = datetime.strptime(issued_at_raw, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="issued_at must be YYYY-MM-DD")


    assignee = None
    if assignee_id_raw:
        assignee = db.get(models.MRAssignee, int(assignee_id_raw))
    elif new_assignee_name:
        assignee = db.query(models.MRAssignee).filter(models.MRAssignee.name == new_assignee_name).first()
        if not assignee:
            assignee = models.MRAssignee(name=new_assignee_name, initials=new_assignee_initials)
            db.add(assignee)
            db.flush()


    if not assignee:
        raise HTTPException(status_code=400, detail="Select an assignee or add a new one")


    room_id = int(room_id_raw) if room_id_raw else None
    selected_asset_ids = {asset_id}
    selected_asset_ids.update(int(str(v)) for v in asset_ids_raw if str(v).strip())
    selected_assets = db.query(models.Asset).filter(models.Asset.id.in_(sorted(selected_asset_ids))).all()


    if existing_mr_id_raw:
        mr = db.get(models.MemorandumReceipt, int(existing_mr_id_raw))
        if not mr:
            raise HTTPException(status_code=404, detail="Existing MR not found")
        if reference_no != mr.reference_no:
            conflict = db.query(models.MemorandumReceipt).filter(models.MemorandumReceipt.reference_no == reference_no).first()
            if conflict:
                raise HTTPException(status_code=409, detail="Reference number already exists")
    else:
        conflict = db.query(models.MemorandumReceipt).filter(models.MemorandumReceipt.reference_no == reference_no).first()
        if conflict:
            raise HTTPException(status_code=409, detail="Reference number already exists")
        mr = models.MemorandumReceipt(reference_no=reference_no, issued_to=assignee.name)
        db.add(mr)


    mr.reference_no = reference_no
    mr.issued_to = assignee.name
    mr.assignee_id = assignee.id
    mr.issued_by = issued_by
    mr.issued_at = issued_at
    mr.status = status
    mr.room_id = room_id
    mr.notes = notes
    mr.assets.clear()
    mr.assets.extend(selected_assets)


    db.add(
        models.ActivityLog(
            action="memorandum_receipt_upsert",
            user_id=user.id,
            details=f"MR {reference_no} saved for {assignee.name} with {len(selected_assets)} assets",
        )
    )
    db.commit()
    return RedirectResponse(url="/memorandum-receipts", status_code=302)




@router.get("/memorandum-receipts/create", response_class=HTMLResponse)
def mr_create_form(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    assignees = db.query(models.MRAssignee).order_by(models.MRAssignee.name.asc()).all()
    rooms = db.query(models.Room).order_by(models.Room.name.asc()).all()
    all_assets = db.query(models.Asset).order_by(models.Asset.name.asc()).all()


    return templates.TemplateResponse(
        "mr_form.html",
        {
            "request": request,
            "title": "Create Memorandum Receipt",
            "user": user,
            "breadcrumbs": _breadcrumbs(
                ("Dashboard", "/dashboard"),
                ("Memorandum Receipts", "/memorandum-receipts"),
                ("Create", None),
            ),
            "assignees": assignees,
            "rooms": rooms,
            "all_assets": all_assets,
            "mr": None,
            "form_action": "/memorandum-receipts/save",
            "form_verb": "Create MR",
        },
    )




@router.get("/memorandum-receipts/{mr_id}", response_class=HTMLResponse)
def mr_detail_view(
    mr_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    mr = db.get(models.MemorandumReceipt, mr_id)
    if not mr:
        raise HTTPException(status_code=404, detail="MR not found")


    user_roles = {r.name for r in user.roles}
    can_edit = bool({"admin", "technician"} & user_roles)
    is_admin = "admin" in user_roles


    asset_rows = []
    for a in mr.assets:
        asset_rows.append(
            {
                "id": a.id,
                "public_id": _public_asset_id(a),
                "name": a.name,
                "category": _asset_category(a),
                "serial_number": a.serial_number or "-",
                "room_name": a.room.name if a.room else "-",
                "status": a.status or "-",
                "status_display": _status_display(a.status),
                "specs": a.specs or "-",
                "tag_status": _asset_tag_status(a),
            }
        )


    return templates.TemplateResponse(
        "mr_detail.html",
        {
            "request": request,
            "title": f"MR {mr.reference_no}",
            "user": user,
            "breadcrumbs": _breadcrumbs(
                ("Dashboard", "/dashboard"),
                ("Memorandum Receipts", "/memorandum-receipts"),
                (mr.reference_no, None),
            ),
            "mr": mr,
            "issued_to": mr.assignee.name if mr.assignee else mr.issued_to,
            "room_name": mr.room.name if mr.room else "-",
            "asset_rows": asset_rows,
            "asset_count": len(asset_rows),
            "can_edit": can_edit,
            "is_admin": is_admin,
        },
    )




@router.get("/memorandum-receipts/{mr_id}/edit", response_class=HTMLResponse)
def mr_edit_form(
    mr_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    mr = db.get(models.MemorandumReceipt, mr_id)
    if not mr:
        raise HTTPException(status_code=404, detail="MR not found")


    assignees = db.query(models.MRAssignee).order_by(models.MRAssignee.name.asc()).all()
    rooms = db.query(models.Room).order_by(models.Room.name.asc()).all()
    all_assets = db.query(models.Asset).order_by(models.Asset.name.asc()).all()


    return templates.TemplateResponse(
        "mr_form.html",
        {
            "request": request,
            "title": f"Edit MR — {mr.reference_no}",
            "user": user,
            "breadcrumbs": _breadcrumbs(
                ("Dashboard", "/dashboard"),
                ("Memorandum Receipts", "/memorandum-receipts"),
                (mr.reference_no, None),
            ),
            "assignees": assignees,
            "rooms": rooms,
            "all_assets": all_assets,
            "mr": mr,
            "form_action": f"/memorandum-receipts/{mr.id}/save",
            "form_verb": "Update MR",
        },
    )




@router.post("/memorandum-receipts/save")
@router.post("/memorandum-receipts/{mr_id}/save")
async def mr_save(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
    mr_id: int | None = None,
):
    role_names = {r.name for r in user.roles}
    if not ({"admin", "technician"} & role_names):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


    form = await request.form()
    reference_no = str(form.get("reference_no", "")).strip()
    issued_by = str(form.get("issued_by", "")).strip() or None
    issued_at_raw = str(form.get("issued_at", "")).strip()
    status = str(form.get("status", "active")).strip() or "active"
    notes = str(form.get("notes", "")).strip() or None
    room_id_raw = str(form.get("room_id", "")).strip()
    assignee_id_raw = str(form.get("assignee_id", "")).strip()
    new_assignee_name = str(form.get("new_assignee_name", "")).strip()
    new_assignee_initials = str(form.get("new_assignee_initials", "")).strip() or None
    asset_ids_raw = form.getlist("asset_ids")


    if not reference_no or not issued_at_raw:
        raise HTTPException(status_code=400, detail="Reference number and issued date are required")


    try:
        issued_at = datetime.strptime(issued_at_raw, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Issued date must be YYYY-MM-DD")


    # Resolve assignee
    assignee = None
    if assignee_id_raw:
        assignee = db.get(models.MRAssignee, int(assignee_id_raw))
    elif new_assignee_name:
        assignee = db.query(models.MRAssignee).filter(models.MRAssignee.name == new_assignee_name).first()
        if not assignee:
            assignee = models.MRAssignee(name=new_assignee_name, initials=new_assignee_initials)
            db.add(assignee)
            db.flush()


    if not assignee:
        raise HTTPException(status_code=400, detail="Select an assignee or add a new one")


    room_id = int(room_id_raw) if room_id_raw else None
    selected_asset_ids = {int(str(v)) for v in asset_ids_raw if str(v).strip()}
    selected_assets = db.query(models.Asset).filter(models.Asset.id.in_(sorted(selected_asset_ids))).all() if selected_asset_ids else []


    if mr_id:
        mr = db.get(models.MemorandumReceipt, mr_id)
        if not mr:
            raise HTTPException(status_code=404, detail="MR not found")
        if reference_no != mr.reference_no:
            conflict = db.query(models.MemorandumReceipt).filter(
                models.MemorandumReceipt.reference_no == reference_no
            ).first()
            if conflict:
                raise HTTPException(status_code=409, detail="Reference number already exists")
    else:
        conflict = db.query(models.MemorandumReceipt).filter(
            models.MemorandumReceipt.reference_no == reference_no
        ).first()
        if conflict:
            raise HTTPException(status_code=409, detail="Reference number already exists")
        mr = models.MemorandumReceipt(reference_no=reference_no, issued_to=assignee.name)
        db.add(mr)


    mr.reference_no = reference_no
    mr.issued_to = assignee.name
    mr.assignee_id = assignee.id
    mr.issued_by = issued_by
    mr.issued_at = issued_at
    mr.status = status
    mr.room_id = room_id
    mr.notes = notes
    mr.assets.clear()
    mr.assets.extend(selected_assets)


    db.add(models.ActivityLog(
        action="memorandum_receipt_upsert", user_id=user.id,
        details=f"MR {reference_no} saved for {assignee.name} with {len(selected_assets)} assets",
    ))
    db.commit()
    return RedirectResponse(url="/memorandum-receipts", status_code=302)




@router.post("/memorandum-receipts/{mr_id}/delete")
def mr_delete(
    mr_id: int,
    admin_password: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    if "admin" not in {r.name for r in user.roles}:
        raise HTTPException(status_code=403, detail="Admin access required")
    if not verify_password(admin_password, user.password_hash):
        raise HTTPException(status_code=403, detail="Incorrect admin password")


    mr = db.get(models.MemorandumReceipt, mr_id)
    if not mr:
        raise HTTPException(status_code=404, detail="MR not found")


    ref = mr.reference_no
    mr.assets.clear()
    db.delete(mr)
    db.add(models.ActivityLog(
        action="memorandum_receipt_delete", user_id=user.id,
        details=f"Deleted MR {ref}",
    ))
    db.commit()
    return RedirectResponse(url="/memorandum-receipts", status_code=302)




@router.get("/ui/tags", response_class=HTMLResponse)
def tags_ui(request: Request, db: Session = Depends(get_db), user: models.User = Depends(current_user_from_cookie)):
    tags = db.query(models.Tag).order_by(models.Tag.created_at.desc()).all()
    assets = db.query(models.Asset).order_by(models.Asset.name.asc()).all()
    rooms = db.query(models.Room).order_by(models.Room.name.asc()).all()
    return templates.TemplateResponse(
        "tags.html",
        {
            "request": request,
            "title": "Tag Linking",
            "user": user,
            "breadcrumbs": _breadcrumbs(("Dashboard", "/dashboard"), ("Tag Linking", None)),
            "tags": tags,
            "assets": assets,
            "rooms": rooms,
        },
    )




@router.post("/ui/tags/create")
def tags_ui_create(
    epc: str = Form(...),
    label: str | None = Form(None),
    status_: str = Form("active", alias="status"),
    asset_id: int | None = Form(None),
    room_id: int | None = Form(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
):
    if "admin" not in {r.name for r in user.roles}:
        raise HTTPException(status_code=403, detail="Admin only")


    exists = db.query(models.Tag).filter(models.Tag.epc == epc).first()
    if exists:
        raise HTTPException(status_code=409, detail="EPC already registered")


    tag = models.Tag(epc=epc.strip(), label=label or None, status=status_, asset_id=asset_id, room_id=room_id)
    db.add(tag)
    db.flush()
    db.add(models.ActivityLog(action="tag_create", user_id=user.id, details=f"Registered EPC {tag.epc}"))
    db.commit()
    return RedirectResponse(url="/ui/tags", status_code=302)




@router.post("/ui/tags/{tag_id}/delete")
def tags_ui_delete(tag_id: int, db: Session = Depends(get_db), user: models.User = Depends(current_user_from_cookie)):
    if "admin" not in {r.name for r in user.roles}:
        raise HTTPException(status_code=403, detail="Admin only")


    tag = db.get(models.Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")


    db.add(models.ActivityLog(action="tag_delete", user_id=user.id, details=f"Deleted EPC {tag.epc}"))
    db.delete(tag)
    db.commit()
    return RedirectResponse(url="/ui/tags", status_code=302)




@router.get("/users/ui", response_class=HTMLResponse)
def users_ui(request: Request, db: Session = Depends(get_db), user: models.User = Depends(current_user_from_cookie)):
    users = db.query(models.User).all()
    return templates.TemplateResponse("users.html", {"request": request, "users": users, "user": user})




@router.get("/inventory", response_class=HTMLResponse)
def inventory(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie),
    q: str | None = Query(default=None),
    sort_by: str = Query(default="id"),
    order: str = Query(default="asc"),
    f_category: str | None = Query(default=None),
    f_room: str | None = Query(default=None),
    f_status: str | None = Query(default=None),
    f_mr: str | None = Query(default=None),
):
    sessions = db.query(models.ScanSession).order_by(models.ScanSession.started_at.desc()).limit(20).all()
    anomalies = db.query(models.Anomaly).order_by(models.Anomaly.last_seen_at.desc()).limit(20).all()
    rooms = db.query(models.Room).order_by(models.Room.name.asc()).all()
    assets_query = db.query(models.Asset)


    # --- text search ---
    if q:
        like = f"%{q.strip()}%"
        assets_query = assets_query.filter(
            (models.Asset.name.like(like))
            | (models.Asset.serial_number.like(like))
            | (models.Asset.location.like(like))
        )


    # --- room filter (server-side, before loading all into memory) ---
    if f_room:
        room_obj = next((r for r in rooms if r.name == f_room), None)
        if room_obj:
            assets_query = assets_query.filter(models.Asset.room_id == room_obj.id)


    # --- status filter (server-side) ---
    if f_status:
        assets_query = assets_query.filter(models.Asset.status == f_status)


    assets = assets_query.all()


    # --- category filter (in-memory, because _asset_category is derived) ---
    if f_category:
        assets = [a for a in assets if _asset_category(a) == f_category]


    # --- MR filter (in-memory) ---
    if f_mr:
        assets = [a for a in assets if _asset_mr_label(a) == f_mr]


    # --- sorting ---
    def sort_key(a: models.Asset):
        if sort_by == "name":
            return (a.name or "").lower()
        if sort_by == "status":
            return (a.status or "").lower()
        if sort_by == "room":
            return (a.room.name if a.room else "").lower()
        if sort_by == "category":
            return _asset_category(a).lower()
        return a.id


    assets.sort(key=sort_key, reverse=(order == "desc"))


    inventory_rows = [
        {
            "id": a.id,
            "public_id": _public_asset_id(a),
            "name": a.name,
            "category": _asset_category(a),
            "room_name": a.room.name if a.room else "-",
            "status": a.status or "-",
            "status_display": _status_display(a.status),
            "mr_label": _asset_mr_label(a),
            "tag_status": _asset_tag_status(a),
        }
        for a in assets
    ]


    # --- build unique filter option lists (from ALL assets, before filters) ---
    all_assets = db.query(models.Asset).all()
    category_options = sorted({_asset_category(a) for a in all_assets})
    room_options = sorted({r.name for r in rooms})
    status_options = [label for _, label in ASSET_STATUS_OPTIONS]
    mr_options = sorted({_asset_mr_label(a) for a in all_assets})


    # Active filters dict for template
    active_filters = {
        "f_category": f_category or "",
        "f_room": f_room or "",
        "f_status": f_status or "",
        "f_mr": f_mr or "",
    }
    active_filter_count = sum(1 for v in active_filters.values() if v)


    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "title": "Inventory Monitoring",
            "user": user,
            "breadcrumbs": _breadcrumbs(("Dashboard", "/dashboard"), ("Inventory Monitoring", None)),
            "sessions": sessions,
            "anomalies": anomalies,
            "rooms": rooms,
            "inventory_rows": inventory_rows,
            "q": q or "",
            "sort_by": sort_by,
            "order": order,
            "category_options": category_options,
            "room_options": room_options,
            "status_options": status_options,
            "mr_options": mr_options,
            "filters": active_filters,
            "active_filter_count": active_filter_count,
        },
    )




@router.get("/schedule")
def get_schedule(request: Request):
    return templates.TemplateResponse("schedule.html", {"request": request})







# Change @app.post to @router.post if the file uses router!
@router.post("/rooms/{room_id}/units/{main_asset_id}/components/{component_id}/edit")
async def edit_component_submit(
    room_id: int,
    main_asset_id: int,
    component_id: int,
    comp_name: str = Form(...),
    comp_status: str = Form(...),
    comp_serial: Optional[str] = Form(None),
    comp_rfid: Optional[str] = Form(None),
    comp_specs: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(current_user_from_cookie)
):
    # Get the component (asset) to update
    component = db.query(models.Asset).filter(models.Asset.id == component_id).first()
    
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    # Update the component fields
    component.name = comp_name
    component.status = comp_status
    if comp_serial:
        component.serial_number = comp_serial
    if comp_rfid:
        component.tag_epc = comp_rfid
    if comp_specs:
        component.specs = comp_specs
    
    # Add activity log
    db.add(models.ActivityLog(
        action="asset_update",
        user_id=user.id,
        asset_id=component_id,
        details=f"Updated component '{comp_name}'"
    ))
    
    # Commit changes
    db.commit()
    
    # Redirect back to the room detail page
    return RedirectResponse(
        url=f"/rooms/{room_id}/units/{main_asset_id}",
        status_code=303
    )




