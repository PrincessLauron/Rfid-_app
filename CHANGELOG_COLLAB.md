# Collaboration Changelog

Use this file as the shared handoff log between Codex and Claude Code.

## Entry Format
- `timestamp`: YYYY-MM-DD HH:MM (local)
- `agent`: Codex | Claude
- `branch`: branch name
- `commit`: hash (or `uncommitted`)
- `scope`: short title
- `files`: key files changed
- `summary`: what changed and why
- `risks_followups`: known issues, migrations, or next actions

---

## Entries

### 2026-02-28 00:00
- agent: Codex
- branch: `codex/pi-mvp-hardening`
- commit: `4e32646`
- scope: MVP hardening baseline
- files:
  - `backend/app/models.py`
  - `backend/app/schemas.py`
  - `backend/app/routers/inventory.py`
  - `backend/app/routers/tags.py`
  - `backend/app/reconciliation.py`
  - `deploy/setup_pi.sh`
  - `deploy/scanner.service`
  - `README.md`
  - `tests/test_api.py`
  - `tests/test_ingest_client.py`
- summary: Implemented ingest reliability, inventory/reconciliation API, admin tag CRUD, Pi deployment updates, and baseline tests.
- risks_followups: Requires migration chain; verify DB state before running app.

### 2026-02-28 00:00
- agent: Codex
- branch: `codex/pi-mvp-hardening`
- commit: `ade263e`
- scope: SQLite migration fix
- files:
  - `backend/migrations/versions/9f12d3b4c5d6_inventory_and_tags.py`
- summary: Fixed SQLite-compatible batch migration behavior.
- risks_followups: Existing partially-migrated local DBs may need reset/rebuild.

### 2026-02-28 00:00
- agent: Codex
- branch: `codex/pi-mvp-hardening`
- commit: `2c57cb4`
- scope: Initial UX revamp
- files:
  - `backend/app/templates/base.html`
  - `backend/app/templates/dashboard.html`
  - `backend/app/templates/room_detail.html`
  - `backend/app/templates/profile.html`
  - `backend/app/static/styles.css`
- summary: Added sidebar, dashboard homepage behavior, room detail page, and profile page.
- risks_followups: Subsequent commits significantly changed IA.

### 2026-02-28 00:00
- agent: Codex
- branch: `codex/pi-mvp-hardening`
- commit: `9c3bf90`
- scope: CCS branding + inventory CSV workflow
- files:
  - `backend/app/templates/base.html`
  - `backend/app/templates/assets_htmx.html`
  - `backend/app/templates/dashboard.html`
  - `backend/app/templates/tags.html`
  - `backend/app/routers/views.py`
  - `backend/app/static/styles.css`
- summary: Applied CCS palette/branding, breadcrumbs, asset-first wording, and CSV import/export actions.
- risks_followups: UX later reworked to reduce clutter.

### 2026-02-28 00:00
- agent: Codex
- branch: `codex/pi-mvp-hardening`
- commit: `aafeffa`
- scope: Sidebar flicker fix
- files:
  - `backend/app/templates/base.html`
  - `backend/app/templates/dashboard.html`
  - `backend/app/routers/views.py`
  - `backend/app/static/styles.css`
- summary: Switched to boosted content-swaps for smoother sidebar navigation.
- risks_followups: Ensure nav active state still updates correctly after future template changes.

### 2026-02-28 00:00
- agent: Codex
- branch: `codex/pi-mvp-hardening`
- commit: `13f9830`
- scope: Memorandum Receipts module
- files:
  - `backend/app/models.py`
  - `backend/app/routers/views.py`
  - `backend/app/templates/memorandum_receipts.html`
  - `backend/migrations/versions/c2a1d9f3b7ee_add_memorandum_receipts.py`
- summary: Added MR tab/page and DB model for MR-to-asset accountability.
- risks_followups: Later extended with assignee directory.

### 2026-02-28 00:00
- agent: Codex
- branch: `codex/pi-mvp-hardening`
- commit: `25c1d60`
- scope: MR workflow simplification
- files:
  - `backend/app/models.py`
  - `backend/app/routers/views.py`
  - `backend/app/templates/memorandum_receipts.html`
  - `backend/app/templates/memorandum_receipt_workflow.html`
  - `backend/migrations/versions/d4e6a1c9b2f0_add_mr_assignees_and_workflow_support.py`
- summary: Converted MR UX to device-first step workflow with assignee names/initials.
- risks_followups: Requires running latest migrations for `assignee_id` support.

### 2026-02-28 00:00
- agent: Codex
- branch: `codex/pi-mvp-hardening`
- commit: `61630d7`
- scope: Full lab page navigation
- files:
  - `backend/app/templates/dashboard.html`
  - `backend/app/templates/room_detail.html`
  - `backend/app/routers/views.py`
  - `backend/app/static/styles.css`
- summary: Dashboard cards open full room pages with scalable filters/pagination.
- risks_followups: Replaced by category-first flow in later commits.

### 2026-02-28 00:00
- agent: Codex
- commit: `26e5ed3`
- branch: `codex/pi-mvp-hardening`
- scope: Room categories + inferred unit sub-assets
- files:
  - `backend/app/routers/views.py`
  - `backend/app/templates/room_detail.html`
- summary: Added category classification and inferred sub-asset views.
- risks_followups: Inference quality depends on naming conventions.

### 2026-02-28 00:00
- agent: Codex
- commit: `d9d6850`
- branch: `codex/pi-mvp-hardening`
- scope: Category-first room UX
- files:
  - `backend/app/routers/views.py`
  - `backend/app/templates/room_detail.html`
  - `backend/app/templates/room_category_detail.html`
  - `backend/app/static/styles.css`
- summary: Room page now opens dedicated category pages with sorting.
- risks_followups: Needed follow-up for AIO unit card flow.

### 2026-02-28 00:00
- agent: Codex
- commit: `75e7699`
- branch: `codex/pi-mvp-hardening`
- scope: AIO/Desktop as unit cards
- files:
  - `backend/app/routers/views.py`
  - `backend/app/templates/room_main_units.html`
  - `backend/app/templates/room_unit_detail.html`
- summary: Main PC categories now show cards per unit; clicking opens sub-asset detail.
- risks_followups: Sub-asset linkage is inferred from naming/location.

### 2026-02-28 00:00
- agent: Codex
- commit: `1da2fc4`
- branch: `codex/pi-mvp-hardening`
- scope: Dashboard AIO focus + inventory editing
- files:
  - `backend/app/models.py`
  - `backend/app/routers/views.py`
  - `backend/app/templates/dashboard.html`
  - `backend/app/templates/inventory.html`
  - `backend/app/templates/asset_edit.html`
  - `backend/migrations/versions/e7b4c1a2d9f8_add_asset_specs_column.py`
- summary: Dashboard shows AIO cards only; inventory moved to table-first page; added specs field, single-edit, and bulk-edit CSV.
- risks_followups: Run migrations before use.

### 2026-02-28 00:00
- agent: Codex
- branch: `codex/pi-mvp-hardening`
- commit: `uncommitted`
- scope: Documentation handoff
- files:
  - `PROJECT_STATUS_AND_PLAN.md`
  - `README_EXECUTIVE_SUMMARY.md`
  - `CHANGELOG_COLLAB.md`
- summary: Added comprehensive project plan/status, executive summary, and shared collaboration changelog.
- risks_followups: Decide whether to commit docs now or after Claude review.

### 2026-02-28 — Session 1
- agent: Claude
- branch: `codex/pi-mvp-hardening`
- commit: `uncommitted`
- scope: Complete UI overhaul — navigation, data cleanup, inline editing, delete with admin password
- files:
  - `backend/app/templates/base.html`
  - `backend/app/templates/dashboard.html`
  - `backend/app/templates/room_detail.html`
  - `backend/app/templates/room_unit_detail.html`
  - `backend/app/templates/inventory.html`
  - `backend/app/templates/asset_edit.html`
  - `backend/app/templates/memorandum_receipts.html`
  - `backend/app/routers/views.py`
  - `backend/app/static/styles.css`
- summary:
  - Redesigned navigation hierarchy: Dashboard (lab cards) -> Room Detail (PC unit cards) -> Unit Detail (component table)
  - Complete CSS design system overhaul with custom properties, modern card styling, stat cards, badges
  - AIO monitor data cleanup — corrected naming conventions for all-in-one PCs
  - Inline status editing via dropdown with auto-submit on component detail pages
  - Admin delete with password confirmation modal for assets/components
  - Breadcrumb navigation throughout all pages
  - htmx-powered SPA-like navigation with content swapping
- risks_followups: Data naming conventions are important for category inference logic

### 2026-02-28 — Session 2
- agent: Claude
- branch: `codex/pi-mvp-hardening`
- commit: `uncommitted`
- scope: Sidebar collapse, sortable/filterable inventory, component CRUD, MR full CRUD
- files:
  - `backend/app/templates/base.html`
  - `backend/app/templates/inventory.html`
  - `backend/app/templates/room_unit_detail.html`
  - `backend/app/templates/memorandum_receipts.html`
  - `backend/app/templates/mr_form.html` (new)
  - `backend/app/routers/views.py`
  - `backend/app/static/styles.css`
- summary:
  - Sidebar collapse/expand toggle with icon-only mode and localStorage persistence
  - Sortable inventory columns (click headers for asc/desc with arrow indicators)
  - 4 filter dropdowns on inventory: Category, Room, Status, MR — with auto-submit
  - Removed redundant Location column from inventory table
  - Fixed sidebar collapsed padding/alignment for symmetric icon centering
  - Fixed brand text overflow with text-overflow: ellipsis
  - Added "Add Component" modal on unit detail page with type/name/serial/status/specs
  - New `COMPONENT_TYPE_CHOICES` constant for component type dropdown
  - Complete MR CRUD: list (MR-centric), create form, edit form, delete with admin password
  - Created shared `mr_form.html` for MR create/edit with recipient, details, and asset selection
- risks_followups: Sort links preserve filter params in URL for consistent UX

### 2026-03-01 — Session 3
- agent: Claude
- branch: `codex/pi-mvp-hardening`
- commit: `uncommitted`
- scope: MR detail page, modal-based asset editing
- files:
  - `backend/app/routers/views.py` — added `/memorandum-receipts/{mr_id}` detail route and `/inventory/assets/{id}/edit-modal` partial endpoint
  - `backend/app/templates/mr_detail.html` (new) — MR detail page with stat cards and asset table
  - `backend/app/templates/_asset_edit_partial.html` (new) — modal-friendly edit form fragment
  - `backend/app/templates/memorandum_receipts.html` — reference number now links to detail page
  - `backend/app/templates/base.html` — added global edit-asset modal container and JS helpers
  - `backend/app/templates/inventory.html` — edit buttons now open modal instead of full page
  - `backend/app/templates/room_unit_detail.html` — edit buttons now open modal instead of full page
  - `backend/app/static/styles.css` — added `.modal-box-wide` class for wider edit modal
- summary:
  - **MR Detail Page**: clicking an MR reference number opens a detail view showing stat cards (reference, issued to, status, date, asset count) and a full table of all assets assigned to that MR with ID, name, category, serial, room, status, specs, and RFID tag status
  - **Modal-Based Asset Editing**: replaced full-page asset edit navigation with an inline modal. Clicking "Edit" on any asset (in inventory or unit detail) opens a modal overlay that fetches the edit form via `/edit-modal` endpoint. The form submits normally and redirects back to the originating page. The partial template `_asset_edit_partial.html` renders without the base layout for clean modal embedding.

### 2026-03-21 15:22
- agent: Codex
- branch: `codex/pi-mvp-hardening`
- commit: `1da2fc4`
- scope: Standalone M7E reader monitor UI + state sync
- files:
  - `reader_standalone/main.py`
  - `reader_standalone/templates/index.html`
  - `reader_standalone/static/style.css`
- summary:
  - Reworked the standalone reader monitor into a two-pane desktop layout with a narrower control rail, lighter workspace, and internal scrolling panes instead of a browser-page-first layout.
  - Reduced typography and control sizing so the app reads more like a dense operator console and less like a generic dashboard.
  - Fixed control-state drift by separating live polling from form sync and persisting user selections locally, so dropdowns no longer snap back to defaults on refresh.
  - Added summary chips for port, mode, and RF profile, plus a cleaner status pill and more compact tags/logs presentation.
  - Kept the current app running on `127.0.0.1:8010` for testing against the updated UI.
- risks_followups:
  - `Single` mode is still app-level auto-stop behavior, not a true reader-level one-shot command yet.
  - UI still needs hardware validation on a real M7E to confirm the final spacing, sizing, and tag-read behavior.
  - If browser cache shows older styling, a hard refresh may be needed after CSS updates.
  - Full edit page (`/inventory/assets/{id}/edit`) is preserved as fallback
  - All 5 existing pytest tests pass
- risks_followups: None identified; all endpoints verified via HTTP smoke tests

### 2026-03-21 — Session 5
- agent: Claude
- branch: `codex/pi-mvp-hardening`
- commit: `uncommitted`
- scope: Handoff from Codex — Claude takes over active development
- files: (pending)
- summary:
  - Reviewed full CHANGELOG and PROJECT_STATUS_AND_PLAN to sync on current state.
  - Codex last touched: `reader_standalone/` — two-pane M7E reader monitor UI with control-state drift fix, summary chips, and compact operator console layout (running on `127.0.0.1:8010`).
  - Claude prior sessions (1–4) covered: full UI overhaul, sidebar collapse, inventory filtering/sort, component CRUD, MR full CRUD, MR detail page, modal-based asset editing, dashboard notifications panel, scan indicators, and Add PC Unit on lab page.
  - Claude is now the active agent. All further work will be logged here.
- risks_followups:
  - reader_standalone needs hardware validation on real M7E.
  - All 5 pytest tests passing per Codex log; verify before any backend changes.
  - Run `alembic upgrade head` before starting the app.

### 2026-03-01 — Session 4
- agent: Claude
- branch: `codex/pi-mvp-hardening`
- commit: `uncommitted`
- scope: Dashboard notifications panel, scan indicators on unit cards, PC unit CRUD on lab page
- files:
  - `backend/app/routers/views.py` — dashboard() adds notification_items + scan_activity; room_detail() adds per-unit anomaly flags + can_edit/is_admin; new POST /rooms/{room_id}/add-unit endpoint
  - `backend/app/templates/dashboard.html` — two-column layout: labs grid (left) + notifications/alerts panel (right)
  - `backend/app/templates/room_detail.html` — Add PC Unit button in header, anomaly banner on alert cards, overlay edit button on unit cards, Add PC Unit modal, unit add form
  - `backend/app/static/styles.css` — new: .dashboard-content, .notif-panel, .notif-*, .tile-card-wrapper, .tile-edit-btn, .tile-card-alert, .unit-alert-banner, .btn-primary
- summary:
  - **Dashboard Notifications Panel**: Sidebar panel showing active RFID scan alerts (missing assets, transfers, incomplete groups) with type, asset name, lab, and relative time. Also shows scan activity per lab with last-scan timestamp and anomaly count badge.
  - **Scan Detection Indicators on Unit Cards**: Each PC unit card on the lab/room detail page shows a red alert banner (e.g., "2 unresolved alerts") when that unit has open anomalies from the RFID system. Card border turns red to draw attention. UI is prepared for live RFID hardware data.
  - **Add/Edit PC Units on Lab Page**: Admins/technicians see an "Add PC Unit" button on the lab detail page header. Clicking opens a modal form to create a new PC unit (name, location/station, serial, status, specs). New units appear automatically in Inventory. An edit button (pencil icon) appears on hover over each unit card, opening the existing asset edit modal.
  - All CRUD on the lab page reflects in Inventory since PC units are Asset records.
  - All 5 pytest tests continue to pass.
- risks_followups: RFID scan data will auto-populate alerts when hardware is connected; no template changes needed — the anomaly model is already queried.

### 2026-05-06 — Reader Standalone Session (Claude)
- agent: Claude
- branch: `feat/reader-standalone-mac-reliability`
- commit: `1b1c0e1`
- scope: Mac-first reliability overhaul for M7E-Nano standalone reader monitor
- PR: https://github.com/JomVill/rfid-ams/pull/1
- files:
  - `reader_standalone/main.py`
  - `reader_standalone/templates/index.html`
  - `reader_standalone/static/style.css`
  - `reader_standalone/debug_terminal.py` (new — CLI raw serial tool)
  - `start_reader_monitor.sh` (new — one-command launcher)
- summary:
  - **Hardware context**: SparkFun M7E-Nano / JADAK ThingMagic, WCH CH340 USB-serial adapter, macOS 26.3.1 Apple Silicon. App runs on `http://127.0.0.1:8010`.
  - **CH340 alias dedup**: WCH adapters enumerate TWO `/dev/cu.*` aliases for the same physical device (`/dev/cu.usbserial-N` and `/dev/cu.wchusbserial-N`). Both share the same USB LOCATION field. Added `_extract_location(hwid)` + `_dedupe_by_location(ports)` to collapse them to one candidate. Without this, baud probing was wasting time probing duplicates and users saw confusing doubled ports.
  - **Ranked port discovery**: `/api/ports` now returns `likely_reader` / `maybe_serial` / `not_reader` categories. Bluetooth and iPhone tether ports are excluded from the default dropdown. Fixed an HTML `<datalist>` prefix-filtering bug (browser was hiding CH340 ports because the input value filtered options) by switching to a proper `<select>`.
  - **Raw (skip-handshake) connect mode**: The user discovered that TX to the module works (setup commands are accepted) but RX from the module returns zero bytes — meaning the module never responds. The handshake (`_try_version_probe`) therefore always times out. Raw mode opens the port and fires the full SparkFun setup sequence fire-and-forget without waiting for ACKs: `stop spam → Gen2 protocol → antenna port → region (PH = 0x12) → read power → disable read filter`. The module receives all config even if we never see a response. `state.connected` is set to `CONNECTED` immediately after.
  - **Honest connection state machine**: Added `DISCONNECTED / OPENING / CONNECTED / STALE / LOST` enum. Heartbeat thread sends a version ping every 5 s during idle; 2 misses → STALE; 3 → LOST. USB yank is now caught in `_read_loop`, flips to LOST, closes the port, and logs the reason. Status pill reflects the real state.
  - **Simplified UI**: Removed the standalone Debug Terminal panel and the Raw Commands section. Merged all hex-send capability into an inline command bar at the top of the Serial Monitor. Collapsed Reader Profile section by default (only Start/Stop/Clear visible). Replaced three buttons (Refresh Ports, Auto Detect, Connect) with a single "Connect to Reader" primary button; Advanced panel discloses manual port + baud + skip-handshake checkbox. Port hint shows candidate count and ticks age every second; auto-refreshes every 2.5 s for hot-plug.
  - **Shared debug send**: Added `_shared_send()` that routes TX through `state._ser` when the main reader holds the port — so the inline hex bar works whether the main reader is connected or the debug session is active.
  - **RX mirroring**: `_read_loop` now mirrors raw RX bytes into `state.logs` (visible in Serial Monitor) when not scanning, in addition to the existing debug session event stream.
  - **Baud sweep widened**: `[115200, 9600, 19200, 38400, 57600, 230400, 460800]` — covers all documented M7E factory baud rates.
  - **Removed Windows residue**: stripped COM/`\\.\` port normalisation branches and Windows hint text. Scope is Mac + Raspberry Pi only.
  - **CLI debug tool**: `reader_standalone/debug_terminal.py` — opens port raw (no handshake), prints every byte as hex+ASCII, accepts hex input to send. Commands: `version`, `stop`, `dtr on|off`, `rts on|off`, `baud <rate>`, `parse on|off`. Useful for verifying the hardware layer independently of FastAPI.
  - **Server port**: app runs on `8010` (not `8765`; a `python3 -m http.server` process was holding 8765).
- risks_followups:
  - **⚠️ ROOT CAUSE NOT FULLY RESOLVED — RX line suspected broken on current test hardware.**
    The module receives TX (setup commands land; confirmed by module-side behavior) but sends back zero bytes — `_try_version_probe` consistently sees no bytes even after 250 ms passive listen and full flush cycles. This strongly suggests a hardware wiring issue on the CH340 adapter: either the RX wire (module TX → CH340 RX) is disconnected, swapped, or on a faulty USB cable (charge-only, data line broken). Codex should **not** spend time chasing software fixes for "no response" — the raw connect mode works around it for now but the underlying serial connection is one-directional.
  - **Action for user before further software work**: test the hardware with `python3 -m reader_standalone.debug_terminal` — if no bytes appear after `stop` + `version` commands, the cable or adapter wiring is the issue. Try a different USB cable (data-capable, not charge-only), different USB-C port, or swap the CH340 breakout.
  - **Handshake mode (normal connect) will remain broken** until RX bytes are confirmed. Raw mode is the working path.
  - **`Single` scan mode** is still app-level auto-stop (issue from prior Codex session), not a true reader one-shot command.
  - Backend changes on `codex/pi-mvp-hardening` (views, templates, styles etc.) are **unstaged** and were intentionally excluded from this PR to keep the reader-standalone changes isolated. They still need a separate commit/PR.
  - `reader_standalone/static/style.css.bak` exists on disk but was excluded from the commit (not needed).
  - Run `start_reader_monitor.sh` (or `uvicorn reader_standalone.main:app --host 0.0.0.0 --port 8010`) to start; the launcher script handles venv activation.

---

### 2026-05-09 — Windows Support (Claude)
- agent: Claude
- branch: `feat/windows-support`
- commit: (see PR)
- scope: Windows setup — COM port support, launchers, requirements, setup guide
- PR: (pending)
- files:
  - `reader_standalone/main.py` — Windows COM port classification + _normalize_port + diagnostics
  - `requirements-windows.txt` (new) — requirements.txt without uvloop
  - `start_webapp.bat` (new) — Windows one-command dashboard launcher
  - `start_reader_monitor.bat` (new) — Windows one-command reader monitor launcher
  - `WINDOWS_SETUP.md` (new) — full Windows setup guide
  - `README.md` — updated with Windows quick start and reference to WINDOWS_SETUP.md
  - `CHANGELOG_COLLAB.md` — this entry
- summary:
  - **`requirements-windows.txt`**: identical to `requirements.txt` minus `uvloop` (Linux/Mac only). Use this file on Windows; the bat scripts use it automatically.
  - **`start_webapp.bat` / `start_reader_monitor.bat`**: same auto-setup behaviour as the `.sh` launchers — venv check, install, migrations, seed, uvicorn start.
  - **Windows COM port support in `reader_standalone/main.py`**:
    - `_READER_PATTERNS`: added `^COM\d+$` and `^\\\\.\\.*COM\d+$` patterns.
    - `_WINDOWS_READER_DESC`: new regex to promote a COM port to `likely_reader` when its description mentions CH340, CH341, FTDI, CP210, Silicon Labs, etc.
    - `_classify_port`: Windows COM port branch — ranks as `likely_reader` if VID boost or desc match, else `maybe_serial`.
    - `_normalize_port`: Windows branch — `COM3` → `COM3`, `COM10` → `\\.\COM10` (high-number ports require the `\\.\` prefix on Windows).
    - `get_diagnostics`: Windows branch — checks `winreg` for `CH341SER` driver key, checks for any COM ports in the port list, generates appropriate issue messages pointing to the WCH driver download.
  - **`WINDOWS_SETUP.md`**: step-by-step for Python install, CH340 driver install, dashboard quickstart, reader monitor COM port setup, raw mode, CLI debug tool, env vars, NSSM service setup, and a troubleshooting table.
  - **`README.md`**: added Windows quick-start table and link to WINDOWS_SETUP.md.
- risks_followups:
  - **Hardware not tested on Windows** — the COM port code paths are correct per pyserial docs and WCH documentation but have not been validated on a real Windows machine with the M7E. Codex or the user should do a smoke test.
  - `uvloop` absence on Windows means slightly lower async throughput; unnoticeable for this use case.
  - `winreg` is only available on Windows — the `get_diagnostics` Windows branch is guarded by `system == "Windows"` so it won't run on Mac/Pi.
  - The Windows service setup (NSSM) in WINDOWS_SETUP.md is optional docs-only — no code changes needed.

---

## Operational Notes For Claude/Codex
- Always run before validation:
  - Mac/Linux: `source .venv/bin/activate && alembic upgrade head`
  - Windows: `.venv\Scripts\activate && alembic upgrade head`
- Use `requirements-windows.txt` on Windows (no `uvloop`).
- MR features rely on migrations:
  - `c2a1d9f3b7ee`
  - `d4e6a1c9b2f0`
- Asset specs and inventory UI rely on migration:
  - `e7b4c1a2d9f8`
- Current branches:
  - `feat/reader-standalone-mac-reliability` — reader standalone (PR #1)
  - `feat/dashboard-ui-overhaul` — dashboard UI (PR #2)
  - `feat/windows-support` — Windows setup (PR #3, pending)
- Main is behind all three PRs; merge order: reader-standalone → dashboard → windows.
