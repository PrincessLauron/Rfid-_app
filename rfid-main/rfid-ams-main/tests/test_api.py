import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app import db, models
from backend.app.security import hash_password


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "test.db"
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        db.engine = engine
        db.SessionLocal = testing_session
        models.Base.metadata.create_all(bind=engine)

        self.client = TestClient(app)
        self._seed_admin()

    def tearDown(self):
        self.client.close()
        self.tmpdir.cleanup()

    def _seed_admin(self):
        session = db.SessionLocal()
        try:
            admin_role = models.Role(name="admin", description="admin")
            tech_role = models.Role(name="technician", description="tech")
            viewer_role = models.Role(name="viewer", description="viewer")
            session.add_all([admin_role, tech_role, viewer_role])
            session.flush()
            admin = models.User(
                username="admin",
                email="admin@example.com",
                password_hash=hash_password("admin123"),
                is_active=True,
            )
            admin.roles.append(admin_role)
            session.add(admin)
            session.commit()
        finally:
            session.close()

    def _auth_headers(self):
        resp = self.client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        self.assertEqual(resp.status_code, 200)
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_admin_tag_crud(self):
        session = db.SessionLocal()
        try:
            room = models.Room(name="Lab A")
            asset = models.Asset(name="PC-1")
            session.add_all([room, asset])
            session.commit()
            room_id = room.id
            asset_id = asset.id
        finally:
            session.close()

        headers = self._auth_headers()
        create_resp = self.client.post(
            "/tags/",
            json={"epc": "E200AAA", "label": "PC Tag", "status": "active", "asset_id": asset_id, "room_id": room_id},
            headers=headers,
        )
        self.assertEqual(create_resp.status_code, 201)
        tag_id = create_resp.json()["id"]

        list_resp = self.client.get("/tags/", headers=headers)
        self.assertEqual(list_resp.status_code, 200)
        self.assertTrue(any(t["epc"] == "E200AAA" for t in list_resp.json()))

        update_resp = self.client.put(f"/tags/{tag_id}", json={"label": "PC Tag Updated"}, headers=headers)
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.json()["label"], "PC Tag Updated")

        delete_resp = self.client.delete(f"/tags/{tag_id}", headers=headers)
        self.assertEqual(delete_resp.status_code, 204)

    def test_missing_after_two_consecutive_scans(self):
        session = db.SessionLocal()
        try:
            room = models.Room(name="Lab B")
            asset = models.Asset(name="Keyboard-1", room=room, component_type="keyboard")
            tag = models.Tag(epc="E200MISS", asset=asset, room=room)
            session.add_all([room, asset, tag])
            session.commit()
            room_id = room.id
            asset_id = asset.id
        finally:
            session.close()

        headers = self._auth_headers()

        s1 = self.client.post("/inventory/sessions", json={"room_id": room_id, "max_unique_tags": 150}, headers=headers)
        self.assertEqual(s1.status_code, 201)
        c1 = self.client.post(f"/inventory/sessions/{s1.json()['id']}/close", headers=headers)
        self.assertEqual(c1.status_code, 200)
        self.assertEqual(c1.json()["missing_asset_ids"], [])

        s2 = self.client.post("/inventory/sessions", json={"room_id": room_id, "max_unique_tags": 150}, headers=headers)
        self.assertEqual(s2.status_code, 201)
        c2 = self.client.post(f"/inventory/sessions/{s2.json()['id']}/close", headers=headers)
        self.assertEqual(c2.status_code, 200)
        self.assertIn(asset_id, c2.json()["missing_asset_ids"])

    def test_incomplete_group_anomaly(self):
        session = db.SessionLocal()
        try:
            room = models.Room(name="Lab C")
            pc = models.Asset(name="PC-1", component_type="pc", room=room, tag_epc="E200PC")
            kb = models.Asset(name="KB-1", component_type="keyboard", room=room, tag_epc="E200KB")
            group = models.AssetGroup(name="Station-1", room=room)
            session.add_all([room, pc, kb, group])
            session.flush()
            session.add_all(
                [
                    models.AssetGroupItem(group=group, required_component="pc", asset=pc, is_required=True),
                    models.AssetGroupItem(group=group, required_component="keyboard", asset=kb, is_required=True),
                ]
            )
            session.commit()
            room_id = room.id
            group_id = group.id
        finally:
            session.close()

        headers = self._auth_headers()
        start = self.client.post("/inventory/sessions", json={"room_id": room_id, "max_unique_tags": 150}, headers=headers)
        self.assertEqual(start.status_code, 201)
        sid = start.json()["id"]

        observe = self.client.post(f"/inventory/sessions/{sid}/observe", json={"epcs": ["E200PC"]}, headers=headers)
        self.assertEqual(observe.status_code, 200)

        close = self.client.post(f"/inventory/sessions/{sid}/close", headers=headers)
        self.assertEqual(close.status_code, 200)
        self.assertEqual(close.json()["incomplete_group_ids"], [group_id])


if __name__ == "__main__":
    unittest.main()
