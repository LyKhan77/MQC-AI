# Direct Inspection Compact Mask Editor

## Goal

Make multi-image polygon masking faster to review with less page scrolling.

## Design

- Keep all staged uploads in a compact horizontal/scrollable thumbnail strip.
- Select one staged image at a time; render one `MaskEditor` only for the selected item.
- Constrain the active editor to a viewport based on available screen height and scroll inside that viewport for unusually tall images.
- Keep image-coordinate polygon behavior unchanged, including Finish, Undo, Clear, status, and full-frame fallback.
- Keep Process QC visible in the compact editor panel and preserve existing result/send-to-QC flow.
- Use existing Carbon tokens, flat geometry, keyboard focus, and no new dependency.

## Success Criteria

- Multiple uploads no longer render multiple large editors vertically.
- Operator can switch images from thumbnails without losing polygon state.
- Active image can be masked without page-level scrolling in normal station viewport.
- Existing Direct Inspection unit and Playwright flows remain green.
