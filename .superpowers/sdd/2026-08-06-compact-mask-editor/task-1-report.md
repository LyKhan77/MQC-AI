# Task 1 Report — Compact Direct Inspection Mask Editor

## Status

Complete.

## Commit

`feat: compact Direct Inspection mask editor`

## Changed files

- `qc_frontend/src/views/DirectInspection.vue`
  - Added stable selected staged-image state.
  - Replaced repeated editors with keyboard-focusable thumbnail buttons and one active `MaskEditor`.
  - Kept the active editor in a `max-height: min(56vh, 560px)` internal viewport with sticky actions.
- `qc_frontend/src/views/__tests__/DirectInspection.test.js`
  - Checks one active editor and thumbnail selection.
- `qc_frontend/tests/e2e/direct-inspection-mask.e2e.js`
  - Checks two staged thumbnails, one editor, and thumbnail switching in the masked/full-frame handoff flow.

## Exact test commands and output

1. `npm test -- src/views/__tests__/DirectInspection.test.js`
   - Initial RED: `1 failed | 12 passed (13)`; the new thumbnail selector returned zero controls on the old layout.
   - Final: `Test Files 1 passed (1)` and `Tests 13 passed (13)`.
2. `npm run test:e2e -- tests/e2e/direct-inspection-mask.e2e.js`
   - Final: `1 passed (8.7s)`.
3. `npm run build`
   - Final: `vite v8.1.0`, `322 modules transformed`, `built in 1.54s`.
4. `npm test`
   - Final: `Test Files 26 passed (26)` and `Tests 142 passed (142)`.
5. `git diff --check`
   - Final: no output; whitespace check passed.

## Self-review

- Adding files selects the first addition only when no active stage exists; removing the active item selects its next sibling, then previous sibling, or clears selection when empty.
- Mask polygons remain stored on their existing staged item; `MaskEditor` receives the same width, height, and model bindings, so coordinate math is unchanged.
- Sequential processing, retry, server/mobile captures, and QC handoff remain on their existing paths.
- Native buttons provide keyboard focus, file-name labels, and pressed state for thumbnail selection.

## Concerns

None. Large source images scroll inside the bounded editor viewport by design; the editor action row remains sticky inside it.
