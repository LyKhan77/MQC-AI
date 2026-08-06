# Direct Inspection Compact Mask Editor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the vertically stacked mask editors with a compact staged thumbnail strip and one bounded active editor.

**Architecture:** Keep staged item state and mask polygons in `DirectInspection.vue`. Add selected-stage navigation and render one existing `MaskEditor`; use scoped CSS for the thumbnail strip, bounded editor viewport, and sticky action area. No backend or API changes.

**Tech Stack:** Vue 3 Composition API, existing `MaskEditor.vue`, vanilla scoped CSS, Vitest, Playwright.

## Global Constraints

- Preserve one polygon per image and existing integer image-coordinate behavior.
- Preserve full-frame fallback, sequential processing, retry, mobile/server camera flows, and QC handoff.
- Use existing CSS variables and no dependency/UI library.
- Keep keyboard focus and accessible labels for stage selection and removal.

---

### Task 1: Compact staged-mask layout

**Files:**
- Modify: `qc_frontend/src/views/DirectInspection.vue`
- Test: `qc_frontend/src/views/__tests__/DirectInspection.test.js`
- Test: `qc_frontend/tests/e2e/direct-inspection-mask.e2e.js`

- [ ] Add selected staged-image state and keep selection valid when files are added or removed.
- [ ] Replace the vertically repeated `MaskEditor` instances with compact selectable thumbnails and one active editor.
- [ ] Bound active editor height to the station viewport and keep actions visible without page-level scrolling.
- [ ] Preserve existing mask/status/process/send behavior and add focused unit/browser assertions for one active editor plus thumbnail switching.
- [ ] Run focused Vitest, Playwright, and production build.
- [ ] Commit `feat: compact Direct Inspection mask editor`.
