# CCS Laboratory Asset Management System

## Project Goal
Build an **asset-first laboratory management system** for CCS where:
- Inventory operations are the primary workflow.
- RFID is a supporting technology (subtle in UI, not dominant).
- Labs can track assets, category views, MR accountability, and anomaly visibility.
- The system scales to large inventories with usable navigation and editing workflows.

## Product Direction (Aligned With Your Requests)
1. Dashboard is the homepage.
2. Sidebar navigation with clean IA and no Users tab.
3. Lab-centric navigation (room-level and category-level).
4. AIO/PC-focused card flow for main units.
5. Inventory table-centric management in Inventory page.
6. MR (Memorandum Receipt) workflow is step-by-step and device-first.
7. Specs support for assets (editable and bulk updatable).
8. CSV import/export as operational workflow.
9. RFID/tag state visible but subtle ("Tagged" / "No tag yet").

---

## Current Architecture
- Backend: FastAPI + Jinja templates
- DB: SQLite + SQLAlchemy + Alembic migrations
- Scanner: pyserial + ingestion client + offline queue
- Deployment target: Raspberry Pi 5 (single-node backend + DB + scanner worker)

Core code paths:
- Backend app: `backend/app`
- Templates: `backend/app/templates`
- Static: `backend/app/static`
- Migrations: `backend/migrations/versions`
- Scanner app: `rfid_app`

---

## Major Features Implemented

### 1. Ingest Reliability and Auth
- Ingest client queues reads on:
  - network exceptions
  - non-2xx backend responses
- Sync deletes only successfully posted queued items.
- Ingest supports either:
  - authenticated admin/technician JWT
  - configured device token for machine ingest

Key files:
- `rfid_app/ingest_client.py`
- `backend/app/deps.py`
- `backend/app/routers/ingest.py`

### 2. Inventory and Reconciliation Domain
Added models and API support for:
- Rooms
- Tags
- Scan sessions and observations
- Asset groups/items
- Anomalies

Reconciliation behavior implemented:
- Missing asset anomaly opens after 2 consecutive misses
- Transfer anomaly on room mismatch
- Incomplete group anomaly support

Key files:
- `backend/app/models.py`
- `backend/app/reconciliation.py`
- `backend/app/routers/inventory.py`
- `backend/migrations/versions/9f12d3b4c5d6_inventory_and_tags.py`

### 3. Admin Tag CRUD
- Full tag registry CRUD support for admin role.
- UI available for tag linking/registry operations.

Key files:
- `backend/app/routers/tags.py`
- `backend/app/templates/tags.html`

### 4. Pi Deployment Hardening
- Service/env-file based runtime setup
- Added scanner worker service
- Setup script runs migration + seed and service configuration

Key files:
- `deploy/backend.service`
- `deploy/scanner.service`
- `deploy/setup_pi.sh`
- `rfid_app/headless_scanner.py`

### 5. CCS Brand/UI Direction
- Branding: CCS Laboratory Asset Management System
- CCS palette integrated
- Sidebar with SVG icons
- Breadcrumb navigation
- Reduced RFID prominence in UX copy and layout

Key files:
- `backend/app/templates/base.html`
- `backend/app/static/styles.css`

### 6. Dashboard + Room IA Evolution
Implemented iterations toward cleaner IA:
- Clickable room cards
- Dedicated room page
- Category-first room navigation
- Category detail pages with sorting
- AIO/PC unit card pages + unit sub-asset detail pages

Current behavior:
- Dashboard now emphasizes **AIO units** in card format.
- Category/table-heavy views are moved to dedicated pages.

Key files:
- `backend/app/templates/dashboard.html`
- `backend/app/templates/room_detail.html`
- `backend/app/templates/room_category_detail.html`
- `backend/app/templates/room_main_units.html`
- `backend/app/templates/room_unit_detail.html`
- `backend/app/routers/views.py`

### 7. Memorandum Receipt (MR) Full CRUD + Detail View
- Full CRUD for MRs: create, read (list + detail), update, delete
- MR list page shows all MRs with reference no, issued to, issued by, date, status, room, asset count
- MR detail page shows stat cards + full table of assigned assets
- MR create/edit form with recipient selection (existing or new), details, and multi-select asset assignment
- MR delete with admin password confirmation modal
- Clickable reference numbers link to detail view
- MR assignee directory with name and initials

Key files:
- `backend/app/templates/memorandum_receipts.html`
- `backend/app/templates/mr_form.html`
- `backend/app/templates/mr_detail.html`
- `backend/app/routers/views.py`
- `backend/app/models.py`
- Migrations below

### 8. Inventory Table + Specs + Editing + Filtering
- Inventory page is table-first for large datasets
- **Sortable columns**: click any column header to sort asc/desc with arrow indicators
- **4 filter dropdowns**: Category, Room, Status, MR — with auto-submit onChange
- **Row selection** with checkboxes and bulk action bar
- **Search toolbar** with Export/Import CSV buttons
- "Clear (N)" button to reset all active filters
- Sort links preserve filter params in URL
- Per-asset specs field, single asset edit (modal), and bulk CSV update endpoint

Key files:
- `backend/app/templates/inventory.html`
- `backend/app/templates/asset_edit.html`
- `backend/app/templates/_asset_edit_partial.html`
- `backend/app/routers/views.py`
- `backend/app/models.py`
- Migration below

### 9a. Sidebar Collapse/Expand
- Toggle button in sidebar header to collapse to icon-only mode (68px width)
- State persisted via localStorage across page loads
- Symmetric padding and centered icons in collapsed state
- Brand text hidden with CSS transitions; nav labels fade out
- User chip and logout text hidden; logout shows icon-only

Key files:
- `backend/app/templates/base.html`
- `backend/app/static/styles.css`

### 9b. Component CRUD on Unit Detail Pages
- "Add Component" button on PC unit detail pages
- Modal form with component type, name, serial number, status, specs
- New component inherits room and location from parent PC unit
- Component type choices: Monitor, Keyboard, Mouse, Adapter, Ethernet Cable
- Existing inline status editing and admin delete preserved

Key files:
- `backend/app/templates/room_unit_detail.html`
- `backend/app/routers/views.py`

### 9c. Modal-Based Asset Editing
- Asset edit opens in an overlay modal instead of full page navigation
- Modal fetches form via `/inventory/assets/{id}/edit-modal` endpoint (returns partial HTML, no base template)
- Form submits via POST and redirects back to the originating page
- Works on both inventory page and unit detail page
- Global modal container in `base.html` with JS helpers
- Full edit page preserved as fallback at `/inventory/assets/{id}/edit`

Key files:
- `backend/app/templates/base.html`
- `backend/app/templates/_asset_edit_partial.html`
- `backend/app/templates/inventory.html`
- `backend/app/templates/room_unit_detail.html`
- `backend/app/routers/views.py`

### 9. CSV Data Import Performed
Imported from:
- `/Users/jomvill/Downloads/Laboratory Inventory Masterlist.csv`

Import result recorded during run:
- Total imported assets: 712
- Includes primary units + sub-assets by row pattern
- Room-mapped to seeded labs

---

## Database Migrations Added
1. `9f12d3b4c5d6_inventory_and_tags.py`
- inventory/tags/anomaly domain

2. `c2a1d9f3b7ee_add_memorandum_receipts.py`
- MR tables and mapping

3. `d4e6a1c9b2f0_add_mr_assignees_and_workflow_support.py`
- MR assignee table + relation

4. `e7b4c1a2d9f8_add_asset_specs_column.py`
- `assets.specs` column

---

## Testing and Validation
Automated checks run repeatedly during implementation:
- `python -m unittest discover -s tests -q`

Coverage includes:
- ingest queue behavior on HTTP/network failures
- admin tag CRUD
- missing anomaly behavior across scans
- incomplete group behavior

Smoke checks used:
- `/health`
- `/dashboard`
- `/rooms/{id}` and category routes
- MR pages and MR creation flow
- CSV export endpoint

---

## Current UX/Data Gaps (Known)
1. Unit-to-sub-asset mapping for PC/AIO is currently inferred from naming/location conventions, not a strict explicit relation model.
2. ~~Dashboard/room IA has improved but still needs final visual polish pass for density/consistency.~~ **Resolved**: Complete UI overhaul with modern card styling, stat cards, badges, and consistent design system.
3. ~~MR and tag flows exist but can be further simplified in interaction language.~~ **Resolved**: Full MR CRUD with detail view, create/edit form, delete with admin password. MR is now MR-centric (not asset-centric).
4. Existing imported specs are incomplete (many rows need manual/bulk enrichment).
5. Component CRUD currently supports adding components but edit/delete of individual components is done through the asset edit modal.

---

## Recommended Next Milestone
### Milestone: “Operational Clean UX + Data Quality Pass”
1. Finalize IA rules:
- Dashboard: AIO main cards only
- Inventory: full tables + bulk operations only
- Category pages: clear, stable sorting and paging

2. Data normalization pass:
- standard naming for units/sub-assets
- fill missing specs for priority assets
- validate MR assignee list

3. Bulk update workflow hardening:
- downloadable bulk-edit template
- import preview/dry-run before apply

4. UI polish:
- tighter spacing
- consistent typographic hierarchy
- reduce secondary text noise

---

## Runbook (Local)
```bash
cd "/Users/jomvill/Developer/RFID AMS"
source .venv/bin/activate
alembic upgrade head
python -m backend.app.seed
uvicorn backend.app.main:app --reload
```

Open:
- `/login`
- `/dashboard`
- `/inventory`
- `/memorandum-receipts`

---

## Branch / Commit Context
Active implementation branch:
- `codex/pi-mvp-hardening`

Recent high-impact commits include:
- MVP hardening (ingest, inventory, deployment, tests)
- CCS UI refocus and breadcrumb/sidebar updates
- MR module and workflow redesign
- category-based room navigation
- dashboard AIO refocus + specs editing + bulk CSV update

