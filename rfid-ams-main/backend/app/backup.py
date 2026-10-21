import argparse
import json
import os
import shutil
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from .db import SessionLocal, engine, DEFAULT_SQLITE_PATH
from . import models


def backup_sqlite(dst_dir: str) -> str:
    os.makedirs(dst_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dst = os.path.join(dst_dir, f"ams-backup-{timestamp}.db")
    shutil.copy2(DEFAULT_SQLITE_PATH, dst)
    return dst


def export_json(dst_path: str) -> None:
    db: Session = SessionLocal()
    try:
        payload: dict[str, Any] = {
            "users": [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "is_active": u.is_active,
                    "roles": [r.name for r in u.roles],
                    "created_at": u.created_at.isoformat(),
                }
                for u in db.query(models.User).all()
            ],
            "roles": [{"id": r.id, "name": r.name, "description": r.description} for r in db.query(models.Role).all()],
            "assets": [
                {
                    "id": a.id,
                    "name": a.name,
                    "serial_number": a.serial_number,
                    "tag_epc": a.tag_epc,
                    "location": a.location,
                    "status": a.status,
                    "component_type": a.component_type,
                    "room_id": a.room_id,
                    "created_at": a.created_at.isoformat(),
                    "updated_at": a.updated_at.isoformat() if a.updated_at else None,
                }
                for a in db.query(models.Asset).all()
            ],
            "rooms": [
                {"id": r.id, "name": r.name, "code": r.code, "created_at": r.created_at.isoformat()}
                for r in db.query(models.Room).all()
            ],
            "tags": [
                {
                    "id": t.id,
                    "epc": t.epc,
                    "label": t.label,
                    "status": t.status,
                    "asset_id": t.asset_id,
                    "room_id": t.room_id,
                    "created_at": t.created_at.isoformat(),
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                }
                for t in db.query(models.Tag).all()
            ],
        }
        with open(dst_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    finally:
        db.close()


def import_json(src_path: str) -> None:
    with open(src_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    db: Session = SessionLocal()
    try:
        # Roles
        name_to_role: dict[str, models.Role] = {}
        for item in data.get("roles", []):
            role = db.query(models.Role).filter_by(name=item["name"]).first()
            if not role:
                role = models.Role(name=item["name"], description=item.get("description"))
                db.add(role)
                db.flush()
            name_to_role[role.name] = role
        # Users (basic upsert without password)
        for item in data.get("users", []):
            user = db.query(models.User).filter_by(username=item["username"]).first()
            if not user:
                continue  # skip create to avoid password issues
            # Update roles
            user.roles.clear()
            for rname in item.get("roles", []):
                role = name_to_role.get(rname)
                if role:
                    user.roles.append(role)
        # Assets (upsert by id)
        for item in data.get("assets", []):
            asset = db.get(models.Asset, item["id"])
            if not asset:
                asset = models.Asset(
                    id=item["id"],
                    name=item["name"],
                    serial_number=item.get("serial_number"),
                    tag_epc=item.get("tag_epc"),
                    location=item.get("location"),
                    status=item.get("status"),
                )
                db.add(asset)
            else:
                asset.name = item["name"]
                asset.serial_number = item.get("serial_number")
                asset.tag_epc = item.get("tag_epc")
                asset.location = item.get("location")
                asset.status = item.get("status")
                asset.component_type = item.get("component_type")
                asset.room_id = item.get("room_id")

        # Rooms
        for item in data.get("rooms", []):
            room = db.get(models.Room, item["id"])
            if room:
                room.name = item["name"]
                room.code = item.get("code")
                continue
            db.add(models.Room(id=item["id"], name=item["name"], code=item.get("code")))

        # Tags
        for item in data.get("tags", []):
            tag = db.get(models.Tag, item["id"])
            if tag:
                tag.epc = item["epc"]
                tag.label = item.get("label")
                tag.status = item.get("status", "active")
                tag.asset_id = item.get("asset_id")
                tag.room_id = item.get("room_id")
                continue
            db.add(
                models.Tag(
                    id=item["id"],
                    epc=item["epc"],
                    label=item.get("label"),
                    status=item.get("status", "active"),
                    asset_id=item.get("asset_id"),
                    room_id=item.get("room_id"),
                )
            )
        db.commit()
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="AMS Backup/Export/Import")
    sub = parser.add_subparsers(dest="cmd")
    b = sub.add_parser("backup", help="Backup sqlite database")
    b.add_argument("--out", default="backups", help="Output directory")

    ej = sub.add_parser("export-json", help="Export core tables to JSON")
    ej.add_argument("--out", default="export.json", help="Output JSON path")

    ij = sub.add_parser("import-json", help="Import core tables from JSON")
    ij.add_argument("--src", required=True, help="Source JSON path")

    args = parser.parse_args()
    if args.cmd == "backup":
        path = backup_sqlite(args.out)
        print(f"Backup created: {path}")
    elif args.cmd == "export-json":
        export_json(args.out)
        print(f"Export written: {args.out}")
    elif args.cmd == "import-json":
        import_json(args.src)
        print("Import complete")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
