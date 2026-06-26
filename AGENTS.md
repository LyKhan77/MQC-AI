# MQC-AI — Agent & Project Operating Manual

<!-- LIVING DOCUMENT: All sections above the ==== divider are [KEEP UPDATED]. -->
<!-- Edit them whenever the codebase changes. See "Documentation Maintenance"  -->
<!-- at the bottom of this file for the update protocol.                       -->
<!-- The RULES section and behavioral guidelines below the ==== dividers are    -->
<!-- generic agent rules and should not be edited.                              -->

README.md is the canonical, detailed project doc. AGENTS.md orients an agent fast. CHANGELOG.md is the detailed change memory. Most sections below summarize README and link to it.

---

## Project Overview · `[KEEP UPDATED]`

**MQC-AI (Manufacturing Quality Control AI)** is an end-to-end computer vision system for automating defect detection in industrial production lines (coating and welding). Built for GSPE.

The system has three decoupled components managed in one monorepo:

1. **`qc_frontend/`** — Interactive dashboard for live camera monitoring and batch QC inspection review. **(Active development)**
2. **`qc_server/`** — Backend SAM3 server for async batch defect segmentation. **(Not yet started)**
3. **`edge_app/`** — Jetson Nano edge app for real-time object detection (YOLO) and live streaming. **(Not yet started)**

**End-to-end workflow**: Edge app detects objects on the production line and live-streams to the dashboard. Inspector monitors the live feed, triggers batch processing, reviews SAM3 segmentation results in QC Studio, and exports PDF audit reports.

Full specs: [`docs/PRD.md`](./docs/PRD.md) | [`docs/workflow.md`](./docs/workflow.md)

---

## Tech Stack · `[KEEP UPDATED]`

### Frontend (`qc_frontend/`)

| Layer | Technology | Version |
|---|---|---|
| Framework | Vue 3 (Composition API, `<script setup>`) | ^3.5 |
| Build tool | Vite | ^8.1 |
| Router | Vue Router | ^4.6 |
| Fonts | IBM Plex Sans + IBM Plex Mono (`@fontsource`) | ^5.2 |
| PDF generation | jsPDF (dynamic import) | ^4.2 |
| Testing | Vitest | ^4.1 |
| CSS | Vanilla CSS with CSS Variables (no Tailwind, no UI library) | — |
| Design system | Carbon Design System (IBM) with light/dark mode | — |

### Backend (`qc_server/` — planned)

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| ML framework | PyTorch |
| Segmentation model | SAM3 |

### Edge (`edge_app/` — planned)

| Layer | Technology |
|---|---|
| Runtime | Python |
| Inference | TensorRT |
| Video | OpenCV |
| Stream server | Flask / FastAPI (MJPEG / WebSocket / WebRTC) |

---

## Key Features · `[KEEP UPDATED]`

### Frontend (current)

- **Sidebar navigation shell** (collapsible) with 6 pages.
- **Live Monitor**: camera selector (RaspyCam/RTSP/USB), Start/Stop detection trigger, mock object counter, FPS/temperature, Send to QC dialog with batch name + auto-timestamp.
- **QC Studio**: 3-column layout with batch sidebar (filter/search/sort/skeleton loading), inspection canvas (zoom/pan/annotation toggle), defect panel (keyboard navigation, review workflow).
- **Batch History**: searchable/filterable table of all processed batches, click to reopen in QC Studio.
- **Reports**: PDF audit report generator (batch summary, defect table, signature/approval fields) via jsPDF.
- **Audit Log**: auto-logged activity trail (all user actions across the app).
- **Settings**: camera CRUD, model config (confidence threshold, detection/segmentation model), preferences (language, theme).
- **Bilingual i18n** (Bahasa Indonesia / English) with toggle, persisted in localStorage.
- **Light/Dark mode** toggle (Carbon Gray-100 dark theme), persisted in localStorage.

### Backend (planned — `qc_server` first)

- Async batch **defect** segmentation over folders of crops, via **polling** (`job_id` → poll status).
- **Pluggable defect strategy** selectable from Settings: `mock` → `sam3_prompt` (SAM3 promptable concept segmentation, zero-training) → future `detector_refine` / `anomaly` (anomalib).
- **SQLite** for queryable metadata (batches/images/defects/cameras/audit/settings/defect_classes) + filesystem/NAS for images & result JSON.
- Editable `defect_classes` driving QC batching (replaces frontend's hardcoded defect color map).
- Single-user MVP (auth deferred; reviewer from config).
- Full plan: `docs/superpowers/plans/qc-server-plan.md` (gitignored).

### Edge (planned — after qc_server)

- Real-time **object (product) detection + counting** on Jetson Nano from trained `.pt` (Detection/Segmentation), using `supervision`.
- Per-camera count mode: `tracking` (ByteTrack + LineZone/PolygonZone) or `single` (1-frame-1-object).
- **Count inspection gate**: technician approves count, then triggers `POST /api/batches` with crop folder path.
- Auto-crop detected objects (bbox/mask) to shared NAS storage.
- Live video stream (MJPEG/WebRTC) to dashboard.

---

## Project Structure · `[KEEP UPDATED]`

```
MQC-AI/
├── qc_frontend/               # Vue 3 dashboard (active development)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── public/
│   │   ├── favicon.svg
│   │   └── mock/
│   │       ├── batch-shift1.json    # Mock batch data (3 images)
│   │       └── images/              # Mock product images
│   └── src/
│       ├── main.js                  # App entry
│       ├── App.vue                  # Root: sidebar + topbar shell
│       ├── style.css                # Carbon CSS variables (light/dark) + shared styles
│       ├── router/
│       │   └── index.js             # 6 named routes
│       ├── assets/
│       │   └── locales/
│       │       ├── id.js            # Indonesian translations (~300 strings)
│       │       └── en.js            # English translations
│       ├── components/
│       │   ├── AppSidebar.vue       # Collapsible nav (6 menu items)
│       │   ├── TopBar.vue           # Slim top bar (title, theme, i18n, profile)
│       │   ├── BatchSidebar.vue     # Batch list with filter/search/review progress
│       │   ├── InspectionCanvas.vue # Image canvas with zoom/pan/annotation
│       │   └── DefectPanel.vue      # Defect details + export + keyboard nav
│       ├── composables/
│       │   ├── useTheme.js          # Light/dark theme toggle (localStorage)
│       │   ├── useI18n.js           # ID/EN language toggle (localStorage)
│       │   ├── useInspection.js     # Batch loading, image selection, review workflow
│       │   ├── useCameras.js        # Camera CRUD (localStorage)
│       │   ├── useBatchHistory.js   # Batch history list (localStorage)
│       │   ├── useAuditLog.js       # Audit trail logging (localStorage)
│       │   └── useSettings.js       # Model config + preferences (localStorage)
│       ├── views/
│       │   ├── LiveMonitor.vue      # Camera selector + detection + send-to-QC
│       │   ├── QCStudio.vue         # 3-column inspection studio
│       │   ├── BatchHistory.vue     # Batch table with search/filter
│       │   ├── Reports.vue          # PDF report generator
│       │   ├── AuditLog.vue         # Activity log table
│       │   └── Settings.vue         # Camera CRUD + model config + preferences
│       └── utils/
│           ├── defect.js            # Defect type -> CSS variable color mapping
│           ├── export.js            # Canvas render + crop/full export (dynamic color)
│           └── mockData.js          # Seed data (3 cameras, 5 batches, 15 logs)
├── qc_server/                # Backend SAM3 server (not yet started)
├── edge_app/                 # Jetson Nano edge app (not yet started)
├── docs/
│   ├── PRD.md                # Product Requirements Document
│   ├── workflow.md           # System workflow + architecture diagram
│   └── superpowers/
│       └── plans/            # Implementation plans (gitignored, not committed)
├── DESIGN.md                 # Carbon Design System spec (light/dark tokens)
├── CHANGELOG.md              # Detailed change log + Current Codebase State table
├── README.md                 # Canonical project doc
├── AGENTS.md                 # This file
└── .gitignore
```

---

## Project Commands · `[KEEP UPDATED]`

All commands run from `qc_frontend/` directory.

| Command | Description |
|---|---|
| `npm install` | Install dependencies |
| `npm run dev` | Start Vite dev server (default: `http://localhost:5173`) |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview production build locally |
| `npm test` | Run unit tests (Vitest) |

**Do not change** these command definitions in `package.json` without updating this section.

---

## Coding Conventions · `[KEEP UPDATED]`

### Vue Components

- Use `<script setup>` Composition API (no Options API).
- Import composables at top: `import { useXxx } from '../composables/useXxx.js'`.
- One component per `.vue` file. File name = PascalCase.
- `<style scoped>` always. Use `var(--color-*)` tokens, never raw hex values.

### CSS

- **No Tailwind, no UI libraries.** Vanilla CSS only.
- All colors via CSS variables defined in `style.css` (`--color-primary`, `--color-ink`, etc.).
- Legacy aliases (`--bg-app`, `--text-primary`) map to new Carbon tokens for backward compat.
- `border-radius: 0px` on all components (Carbon flat geometry).
- `letter-spacing: 0.16px` on body text (Carbon precision detail).
- Fonts: `var(--font-sans)` (IBM Plex Sans), `var(--font-mono)` (IBM Plex Mono).

### Composables

- Singleton pattern: module-scoped `ref()` outside the exported function.
- `localStorage` persistence with seed-on-first-load from `mockData.js`.
- Each composable returns refs + methods, no state mutation from outside.

### i18n

- All user-facing text via `t('key.path')` from `useI18n`.
- Translation keys namespaced: `nav.*`, `live.*`, `qc.*`, `batches.*`, `reports.*`, `audit.*`, `settings.*`, `common.*`.
- Add new strings to both `id.js` and `en.js`.

### Defect Colors

- Defined as CSS variables (`--defect-scratch`, `--defect-porosity`, etc.) in `style.css`.
- `utils/defect.js` maps type string to CSS variable name.
- `utils/export.js` resolves via `getComputedStyle` for canvas rendering.
- **Will become dynamic** from SAM3 backend response in the future.

### File Naming

- Views: PascalCase (`LiveMonitor.vue`, `QCStudio.vue`).
- Components: PascalCase (`AppSidebar.vue`, `DefectPanel.vue`).
- Composables: camelCase with `use` prefix (`useTheme.js`, `useInspection.js`).
- Utils: camelCase (`defect.js`, `export.js`, `mockData.js`).
- Locales: lowercase ISO code (`id.js`, `en.js`).

---

## Workflow · `[KEEP UPDATED]`

### End-to-End System Workflow

```
[Camera List] → [Select Camera] → [Start Detection]
    → [Monitor Live Feed + Object Counter]
    → [Send to QC: batch name + timestamp]
    → [SAM3 Batch Processing (backend)]
    → [QC Studio: Review defects + zoom/pan + mark reviewed]
    → [Export: Crop/Full PNG + PDF Audit Report]
    → [Audit Log: auto-trails all actions]
```

### Development Workflow (for AI agents)

1. Read `CHANGELOG.md` to understand current state.
2. Read the relevant section in this file.
3. Check `docs/superpowers/plans/` for any active implementation plan.
4. Make changes following Coding Conventions above.
5. Run `npm run build` and `npm test` to verify.
6. Update `CHANGELOG.md` with a new entry (see protocol at bottom of CHANGELOG.md).
7. Update relevant `[KEEP UPDATED]` sections in this file.
8. Update `README.md` if key features or architecture changed.
9. Commit with a descriptive message.

---

## Current State · `[KEEP UPDATED]`

### Status: Frontend Active Development · Backend Planning Approved

**What is being developed now**: Frontend UI dashboard with mock data. All 6 pages are functional with mock data layer and localStorage persistence. **Backend (`qc_server`) architecture is planned and approved** (see `docs/superpowers/plans/qc-server-plan.md`); implementation pending (milestones M0→M4). Edge app (Jetson) comes after `qc_server`.

### Component Status

| Component | Status | Description |
|---|---|---|
| `qc_frontend/` | **Active** | 6 pages, Carbon Design System, i18n, mock data. All UI functional with mock data. |
| `qc_server/` | **Not started** | FastAPI + SAM3 batch segmentation server. Planned. |
| `edge_app/` | **Not started** | Jetson Nano YOLO detection + live streaming. Planned. |

### Frontend Page Status

| Page | Status | Mock Data | Backend Ready |
|---|---|---|---|
| Live Monitor | **Functional** | Mock detection loop, 3 cameras | Needs Jetson stream endpoint |
| QC Studio | **Functional** | Mock batch JSON (3 images) | Needs SAM3 server endpoint |
| Batch History | **Functional** | 5 mock batches in localStorage | Needs batch persistence API |
| Reports | **Functional** | Uses mock batch data | Needs batch data API |
| Audit Log | **Functional** | 15 mock entries in localStorage | Needs audit persistence API |
| Settings | **Functional** | 3 mock cameras in localStorage | Needs camera config API |

### Detailed Log

See [`CHANGELOG.md`](./CHANGELOG.md) for the comprehensive, per-feature change log with Current Codebase State tables.

**Latest version**: [0.2.0] - 2026-06-26 (Full frontend overhaul: Carbon Design System, sidebar nav, 6 pages, i18n, mock data layer).

---

## Documentation Maintenance

**This protocol is mandatory for all AI agents.**

### When to Update

Update these documents **after every committed change**:

1. **`CHANGELOG.md`** — Always. Append a new entry per feature/file logic. Follow the format at the bottom of CHANGELOG.md. Include the Current Codebase State table.
2. **`AGENTS.md`** — Update any `[KEEP UPDATED]` section that is now inaccurate. Particularly: Project Structure (files added/removed), Key Features (new feature), Current State (status changed), Tech Stack (new dependency), Project Commands (new script), Coding Conventions (new pattern).
3. **`README.md`** — Update when key features, architecture, or workflow change. Keep the canonical doc in sync.

### Update Protocol

```
1. Make code changes
2. Run `npm run build` + `npm test` → verify pass
3. Commit code
4. Append entry to CHANGELOG.md (per-feature granularity)
5. Update AGENTS.md [KEEP UPDATED] sections if affected
6. Update README.md if architecture/features changed
7. Commit documentation changes (separate from code commit is fine)
```

### What NOT to Do

- Do not delete historical CHANGELOG entries. Append only.
- Do not commit `docs/superpowers/plans/` or `docs/superpowers/specs/` (gitignored).
- Do not change the RULES section below the ==== divider.
- Do not skip CHANGELOG update. It is the agent memory contract.

===========================

# RULES - DO NOT CHANGE or EDIT this Section

## Important Notes - Project RULES

- Always use relevant skills to help with tasks.
- Always ask the user if there are any plans or discussions that need to be validated.
- Always provide a summary after finishing a task.
- Always update `README.md` whenever there are changes to key features and the app's workflow. Please note the section commands that must not be changed.
- Commit every function change so you can roll back and view the code history in case of a malfunction or a failed change. Also UPDATE the `.gitignore` file whenever a new file is added that needs to be excluded before committing.
- Do not re-read files that have already been read in this session unless necessary.
- Minimize non-essential tool calls.
- Save every plan or specification to the `docs\superpowers\plans` and `docs\superpowers\specs` folder so you can track which plans have been created or are currently being created. This allows you to resume the session if the AI agent's token expires. USE `Superpowers` skill to provide the plan. REMEMBER This file does not need to be updated unless requested. It is intended solely as a record of past information. Make sure not to DUPLICATE it; if you've already created a plan outside of Superpowers, there's no need to create another one, and vice versa.
- DO NOT commit the Plans.

===========================

# AGENTS.md — DO NOT EDIT BELOW

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
