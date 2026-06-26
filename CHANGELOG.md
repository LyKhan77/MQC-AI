# CHANGELOG

> **Agent Memory Contract.** This file is the single source of truth for what changed, when, and why. Every AI agent working on this repo MUST read this file before starting work and MUST append an entry after committing changes. See `AGENTS.md` section "Documentation Maintenance" for the full contract.

All notable changes to the MQC-AI project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [Semantic Versioning](https://semver.org/).

Each entry contains:
1. Standard Keep a Changelog categories (Added / Changed / Fixed / Removed)
2. **Current Codebase State** table tracing what was developed and the resulting state

---

## [0.2.0] - 2026-06-26

### Summary

Full frontend overhaul: Carbon Design System migration (light/dark), sidebar navigation shell, 6 routed pages, i18n bilingual, rich mock data layer, and P0 bug fixes.

### Added

- **Carbon Design System** with light mode (default) and dark mode (Carbon Gray-100 theme).
  - CSS variables for both themes in `style.css`, toggled via `data-theme` attribute on `<html>`.
  - IBM Plex Sans (300/400/600) + IBM Plex Mono fonts via `@fontsource`.
  - Flat geometry (0px border-radius), 1px hairline borders, surface hierarchy.

- **Theme toggle** composable (`useTheme.js`).
  - Default follows `prefers-color-scheme`, user can override via toggle button in top bar.
  - Persisted in `localStorage` key `mqc-theme`.

- **Collapsible sidebar navigation** (`AppSidebar.vue`) + slim top bar (`TopBar.vue`).
  - 6 nav items with SVG icons: Live Monitor, QC Studio, Batch History, Reports, Audit Log, Settings.
  - Sidebar collapse/expand button; collapsed state shows icons only (56px width).

- **i18n bilingual system** (Indonesian / English).
  - Composable `useI18n.js`, locale files `src/assets/locales/id.js` and `en.js`.
  - Language toggle in top bar (ID/EN button) and in Settings page.
  - Persisted in `localStorage` key `mqc-lang`.

- **Live Monitor page** (redesigned).
  - Camera selector dropdown (reads from `useCameras` composable).
  - Start/Stop Detection buttons with connecting state.
  - Mock object counter, FPS, temperature indicators with live-updating values.
  - Mock bounding box overlay on video feed placeholder.
  - Send to QC dialog: batch name input with auto-timestamp, source camera, image count, model info.

- **QC Studio page** (redesigned).
  - Batch sidebar: search input, filter chips (All/Defect/Clean/Unreviewed), sort dropdown (name/defect count), skeleton loading state, review progress bar, error display.
  - Inspection canvas: zoom (mouse wheel, 50%-500%), pan (drag), annotation toggle, reset zoom button.
  - Defect panel: keyboard navigation (Arrow keys to navigate images, Spacebar to toggle reviewed).
  - Review workflow: mark/unmark reviewed per image, visual checkmark in batch list, reviewed set persisted in `localStorage`.

- **Batch History page** (new).
  - Table of all processed batches from `useBatchHistory` composable.
  - Search by batch name, filter by status (reviewed/pending/processing).
  - Click row to open batch in QC Studio. Generate Report shortcut.

- **Reports page** (new).
  - Batch selector dropdown.
  - Summary cards: total images, clean, defective, defect rate.
  - Defect detail breakdown per image with color-coded tags.
  - PDF generation via `jspdf`: audit report with batch info, summary, defect table, signature/approval fields.

- **Audit Log page** (new).
  - Table of all activity from `useAuditLog` composable.
  - Search by detail/user, filter by action type.
  - Auto-logs from all user actions (camera start/stop, batch sent/loaded, image reviewed, export, report generated, settings changed, camera CRUD).

- **Settings page** (new).
  - Camera management: table with add/edit/delete (CRUD), camera form (name, type, source, location).
  - Model configuration: detection model, segmentation model, confidence threshold slider.
  - Preferences: language toggle (ID/EN), theme info.

- **Mock data layer** (`utils/mockData.js`).
  - 3 cameras (RaspyCam CSI, RTSP, USB), 5 batch history entries, 15 audit log entries, default settings.
  - All persistent in `localStorage` with seed-on-first-load pattern.

- **5 new composables**: `useI18n.js`, `useCameras.js`, `useBatchHistory.js`, `useAuditLog.js`, `useSettings.js`.

- **`docs/superpowers/plans/frontend-overhaul-plan.md`**: full implementation plan for this overhaul.

### Changed

- **`DESIGN.md`**: replaced GSPE Corporate Dark Theme with Carbon Design System spec. Added light + dark mode token tables, type scale, spacing system, component specs, and implementation rules.

- **`index.html`**: updated `<html lang="id" data-theme="light">`, title to `GSPE MQC-AI Dashboard`.

- **Router** (`router/index.js`): expanded from 2 routes to 6 routes with named routes.

- **`App.vue`**: replaced top-nav horizontal with sidebar + topbar shell layout.

- **`style.css`**: added Carbon CSS variables (light + dark blocks), legacy alias mapping, page-container/page-header shared styles. Removed old top-nav styles.

- **`useInspection.js`**: added `loading`, `error`, `reviewed`, `reviewedCount`, `toggleReviewed`, `isReviewed`. Added simulated network delay (1.2s) and try/catch error handling. Reviewed state persisted in `localStorage`.

### Fixed

- **`export.js` hardcoded defect colors** (P0): `resolveColor()` now reads CSS variables dynamically via `getComputedStyle(document.documentElement).getPropertyValue('--defect-{type}')` instead of hardcoded hex values from the old theme. Fallback chain: CSS var > `--color-ink-subtle` > `#8c8c8c`.

- **Load Batch zero feedback** (P0): added skeleton loading state, simulated network delay, visible error message in sidebar, disabled button during loading.

- **Export silent fail** (P0): added try/catch around `loadImageEl()` in `exportCrop` and `exportFull` with console error logging.

### Removed

- `@fontsource/inter` and `@fontsource/jetbrains-mono` imports from `style.css` (replaced by IBM Plex fonts). Packages remain installed but unused.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Design System | 2026-06-26 | Carbon Design System with light/dark mode tokens | `style.css` has `:root[data-theme='light']` and `:root[data-theme='dark']` blocks; all components use `--color-*` tokens |
| Navigation Shell | 2026-06-26 | Collapsible sidebar + slim top bar | `App.vue` renders `AppSidebar.vue` (220px/56px) + `TopBar.vue` (48px) + `<router-view>` |
| Routing | 2026-06-26 | 6 named routes | `/live`, `/qc`, `/batches`, `/reports`, `/audit`, `/settings`; `/` redirects to `/live` |
| i18n | 2026-06-26 | Bilingual ID/EN with `useI18n` composable | ~300 translation strings in `locales/id.js` and `locales/en.js`; toggle in top bar + Settings |
| Live Monitor | 2026-06-26 | Camera selector + detection trigger + send-to-QC dialog | `LiveMonitor.vue` reads `useCameras`, mock detection loop, `SendToQCDialog` inline modal |
| QC Studio | 2026-06-26 | Review workflow + zoom/pan + filter/search + keyboard nav | `BatchSidebar` has filter chips + skeleton; `InspectionCanvas` has zoom/pan toolbar; `DefectPanel` has arrow/space keyboard handlers |
| Batch History | 2026-06-26 | Table view of all batches | `BatchHistory.vue` reads `useBatchHistory`, search + status filter, row click navigates to QC |
| Reports | 2026-06-26 | PDF audit report generator | `Reports.vue` uses dynamic `import('jspdf')`, generates `{batch_name}_report.pdf` |
| Audit Log | 2026-06-26 | Activity trail table | `AuditLog.vue` reads `useAuditLog`, search + action filter, auto-logged from all composables |
| Settings | 2026-06-26 | Camera CRUD + model config + preferences | `Settings.vue` manages `useCameras`, `useSettings`, `useI18n`; all changes logged via `useAuditLog` |
| Mock Data | 2026-06-26 | Rich mock layer with localStorage persistence | `mockData.js` seeds 3 cameras, 5 batches, 15 logs on first load; composables auto-seed if `localStorage` empty |
| Export Utils | 2026-06-26 | Dynamic CSS variable color resolution | `export.js` `resolveColor()` reads `getComputedStyle` instead of hardcoded hex |

---

## [0.1.0] - 2026-06-25

### Summary

Initial frontend scaffold: Vue 3 + Vite project, 2-page dashboard (Live Monitor + QC Studio), GSPE Corporate Dark Theme, mock batch data.

### Added

- Vue 3 + Vite project with Vue Router.
- `LiveMonitor.vue`: live video feed placeholder with status pill (ONLINE/OFFLINE), FPS/temperature metrics, MJPEG stream URL display.
- `QCStudio.vue`: 3-column layout (BatchSidebar / InspectionCanvas / DefectPanel).
- `BatchSidebar.vue`: Load Batch button, batch list with filename + defect count + status dot.
- `InspectionCanvas.vue`: image display with SVG polygon overlay for defect annotations, hover cross-panel interaction.
- `DefectPanel.vue`: coating/welding defect list with confidence percentage, export crop/full buttons.
- `useInspection.js`: shared singleton state (batch, selectedId, hoveredDefectId, loadBatch, selectImage).
- `utils/defect.js`: defect type to CSS variable color mapping + polygon bounding box utility.
- `utils/export.js`: canvas rendering with polygon overlay, crop/full export with download.
- Mock data: `public/mock/batch-shift1.json` with 3 images (2 defective, 1 clean).
- `DESIGN.md`: GSPE Corporate Dark Theme spec (navy blue palette, gold accent, defect color tokens).
- `docs/PRD.md`: Product Requirements Document.
- `docs/workflow.md`: System workflow and architecture diagram.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Project Scaffold | 2026-06-25 | Vue 3 + Vite + Vue Router | `package.json` with vue@3.5, vite@8, vue-router@4 |
| Frontend Shell | 2026-06-25 | 2-page horizontal nav | `App.vue` with top-nav, `/live` and `/qc` routes |
| QC Studio | 2026-06-25 | 3-column inspection layout | BatchSidebar (280px) + Canvas (flex) + DefectPanel (320px) |
| Mock Data | 2026-06-25 | Single batch JSON | `public/mock/batch-shift1.json` with 3 images, polygon coordinates |
| Design System | 2026-06-25 | GSPE Dark Theme tokens | `style.css` with navy palette (`#031124`, `#06244A`), gold accent, defect colors |

---

## How to Update This File

**Every AI agent MUST follow this protocol when committing changes:**

1. **Read this file first.** Understand what was done before. Do not duplicate entries.
2. **After committing code changes**, append a new entry under `[Unreleased]` (or create a new version section if the user requests a release).
3. **Entry granularity**: one entry per feature, file logic, or significant change. Not per commit, not per session.
4. **Each entry must include**:
   - **Summary**: 1-2 sentence plain-language description.
   - **Added / Changed / Fixed / Removed**: bullet points with specific file names and what changed.
   - **Current Codebase State** table: one row per area affected, with columns `Area / Feature | Timeline | What Was Developed | After the Change`.
5. **Link the entry** in `AGENTS.md` > `Current State` > `Detailed Log` pointer.
6. **Be specific**: file names, composable names, CSS variable names, route names. Vague entries like "improved UI" are useless to the next agent.
7. **Do not delete historical entries.** Append only. Mistakes are corrected in new entries, not by rewriting old ones.
