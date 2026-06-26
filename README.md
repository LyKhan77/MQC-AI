# MQC-AI (Manufacturing Quality Control AI)

## Project Overview

MQC-AI adalah sistem inspeksi kualitas produk berbasis *Computer Vision* end-to-end yang dirancang untuk otomasi deteksi cacat di lini produksi industri (misal: pelapisan/coating dan pengelasan). Proyek ini merupakan inisiatif untuk GSPE.

Sistem ini menggunakan arsitektur *decoupled* yang dipisahkan menjadi 3 komponen utama, namun dikelola dalam satu *repository* (monorepo). Inspector memantau live feed dari kamera, trigger pengiriman batch ke server SAM3 untuk analisis, lalu me-review hasil segmentasi cacat dan generate laporan audit.

## Arsitektur & Workspace

| Component | Status | Description |
|---|---|---|
| `qc_frontend/` | **Active** | Vue 3 dashboard dengan 6 halaman, Carbon Design System, i18n bilingual, mock data layer |
| `qc_server/` | Planned | FastAPI + PyTorch + SAM3 untuk async batch defect segmentation |
| `edge_app/` | Planned | Jetson Nano + TensorRT + OpenCV untuk real-time YOLO detection dan live streaming |

### End-to-End Workflow

```
[Select Camera] → [Start Detection] → [Monitor Live Feed + Object Counter]
    → [Send to QC: batch name + auto-timestamp]
    → [SAM3 Batch Processing]
    → [QC Studio: Review defects (zoom/pan) + mark reviewed]
    → [Export: Crop/Full PNG + PDF Audit Report]
    → [Audit Log: auto-trails all actions]
```

Detail: [`docs/workflow.md`](./docs/workflow.md) | [`docs/PRD.md`](./docs/PRD.md)

## Frontend Dashboard (`qc_frontend/`)

### Tech Stack

- **Vue 3** (Composition API, `<script setup>`) + **Vite** + **Vue Router**
- **Carbon Design System** (IBM) dengan light mode (default) dan dark mode (Gray-100 theme)
- **Vanilla CSS** dengan CSS Variables (no Tailwind, no UI library)
- **IBM Plex Sans** + **IBM Plex Mono** fonts
- **jsPDF** untuk PDF audit report generation
- **Vitest** untuk unit testing

### Pages (6 routes)

| Route | Page | Description |
|---|---|---|
| `/live` | **Live Monitor** | Camera selector (RaspyCam/RTSP/USB), Start/Stop detection, object counter, Send to QC dialog |
| `/qc` | **QC Studio** | 3-column inspection: batch sidebar (filter/search) + canvas (zoom/pan) + defect panel (keyboard nav, review workflow) |
| `/batches` | **Batch History** | Searchable table of all processed batches, filter by status |
| `/reports` | **Reports** | PDF audit report generator with summary, defect table, approval fields |
| `/audit` | **Audit Log** | Auto-logged activity trail, filterable by action type |
| `/settings` | **Settings** | Camera CRUD, model config, language/theme preferences |

### Key Features

- **Bilingual i18n** (Bahasa Indonesia / English) dengan toggle, persisted di localStorage
- **Light/Dark mode toggle** dengan Carbon Gray-100 dark theme, persisted di localStorage
- **Collapsible sidebar navigation** dengan 6 menu items
- **Review workflow**: mark/unmark reviewed per image, progress bar, keyboard navigation
- **Zoom/Pan canvas**: mouse wheel zoom (50%-500%), drag to pan, annotation toggle
- **Rich mock data**: 3 cameras, 5 batch history, 15 audit logs, semua persistent di localStorage
- **Dynamic defect colors**: CSS variable resolution, siap untuk dynamic colors dari SAM3 backend

### Commands

> **Do not change** these command definitions without updating `AGENTS.md`.

| Command | Description |
|---|---|
| `cd qc_frontend && npm install` | Install dependencies |
| `cd qc_frontend && npm run dev` | Start Vite dev server (`http://localhost:5173`) |
| `cd qc_frontend && npm run build` | Production build to `dist/` |
| `cd qc_frontend && npm run preview` | Preview production build |
| `cd qc_frontend && npm test` | Run unit tests (Vitest) |

## Design System

Frontend menggunakan **Carbon Design System** (IBM) dengan prinsip:
- Flat geometry (`border-radius: 0px`) dengan 1px hairline borders
- IBM Plex Sans weight 300 untuk display, 400 untuk body (`letter-spacing: 0.16px`)
- IBM Blue (`#0f62fe`) sebagai single accent color
- Surface hierarchy via `--color-canvas` / `--color-surface-1` / hairlines (no drop shadows)
- Light mode (default) + Dark mode (Carbon Gray-100 theme)

Detail lengkap: [`DESIGN.md`](./DESIGN.md)

## Documentation

| Document | Purpose |
|---|---|
| [`AGENTS.md`](./AGENTS.md) | Agent operating manual (project overview, tech stack, conventions, current state) |
| [`CHANGELOG.md`](./CHANGELOG.md) | Detailed change log with Current Codebase State table (agent memory contract) |
| [`DESIGN.md`](./DESIGN.md) | Carbon Design System spec (colors, typography, components, light/dark tokens) |
| [`docs/PRD.md`](./docs/PRD.md) | Product Requirements Document |
| [`docs/workflow.md`](./docs/workflow.md) | System workflow and architecture diagram |
| `docs/superpowers/plans/` | Implementation plans (gitignored, not committed) |

## Implementation Plans

Rencana implementasi disimpan di `docs/superpowers/plans/`:
- [`frontend-overhaul-plan.md`](./docs/superpowers/plans/frontend-overhaul-plan.md) - Full frontend overhaul (Carbon Design System, 6 pages, i18n, mock data)

---
*Dokumen ini harus selalu diperbarui setiap kali ada penambahan fitur utama atau perubahan arsitektur. Lihat protocol di `AGENTS.md` > Documentation Maintenance.*
