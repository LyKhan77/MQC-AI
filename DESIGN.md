# MQC-AI Dashboard Design System

Sistem desain ini menggunakan **Carbon Design System** (IBM's open-source enterprise design system) dengan dukungan **Light Mode** (default) dan **Dark Mode** (Carbon Gray-100 theme).

## 1. Core Principles

*   **Flat Geometry**: Setiap CTA, card, input, dan container menggunakan sudut kotak (`border-radius: 0px`) dengan border 1px tipis. Tidak ada rounded pills, soft shadows, atau atmospheric gradients.
*   **Light-Weight Display Type**: IBM Plex Sans weight 300 untuk headline ukuran display (42-76px). Weight 400 untuk body dengan `letter-spacing: 0.16px`.
*   **One Accent Color**: IBM Blue (`#0f62fe`) sebagai satu-satunya warna brand. Digunakan untuk primary CTA, links, focus rings, dan CTA banner.
*   **Surface Hierarchy**: Card hierarchy menggunakan 1px hairlines dan surface change (canvas ke surface-1), bukan drop shadows.
*   **Theme Toggle**: Light mode (default) dan Dark mode (Gray-100 theme). Toggle via `data-theme` attribute di `<html>`, persist di `localStorage`.

## 2. Typography

Gunakan **IBM Plex Sans** untuk seluruh hierarchy. **IBM Plex Mono** untuk data angka, file path, dan persentase akurasi.

*   **Primary Font**: `IBM Plex Sans`, fallback: `Helvetica Neue, Arial, sans-serif`.
*   **Mono Font**: `IBM Plex Mono`, fallback: `ui-monospace, monospace`.

### Type Scale

| Token | Size | Weight | Line Height | Letter Spacing | Use |
|---|---|---|---|---|---|
| display-xl | 76px | 300 | 1.17 | -0.5px | Largest hero headline |
| display-lg | 60px | 300 | 1.17 | -0.4px | Section opener headlines |
| display-md | 42px | 300 | 1.20 | 0 | Sub-section headlines |
| headline | 32px | 400 | 1.25 | 0 | Card collection heading |
| card-title | 24px | 400 | 1.33 | 0 | Feature card title |
| subhead | 20px | 400 | 1.40 | 0 | Lead body |
| body-lg | 18px | 400 | 1.50 | 0 | Hero subhead, lead paragraphs |
| body | 16px | 400 | 1.50 | 0.16px | Default body |
| body-sm | 14px | 400 | 1.29 | 0.16px | Card body, footer columns |
| body-emphasis | 14px | 600 | 1.29 | 0.16px | Selected tab, emphasized body |
| caption | 12px | 400 | 1.33 | 0.32px | Captions, meta, utility bar |
| button | 14px | 400 | 1.29 | 0.16px | All button labels |

## 3. Color Tokens (CSS Variables)

### Light Mode (Default)

```css
:root,
:root[data-theme="light"] {
  /* Brand & Accent */
  --color-primary: #0f62fe;        /* IBM Blue */
  --color-primary-hover: #0353e9;  /* Blue Hover */
  --color-primary-pressed: #0043ce;/* Blue 80 */
  --color-on-primary: #ffffff;

  /* Surfaces */
  --color-canvas: #ffffff;         /* Default page background */
  --color-surface-1: #f4f4f4;      /* Light gray - inputs, alternate rows */
  --color-surface-2: #e0e0e0;      /* Disabled fields, separators */
  --color-hairline: #e0e0e0;       /* 1px borders on cards, inputs */
  --color-hairline-strong: #161616;/* Charcoal underline on focused inputs */

  /* Inverse (Footer) */
  --color-inverse-canvas: #161616;    /* Charcoal footer surface */
  --color-inverse-surface-1: #393939; /* Footer dividers, hovered items */

  /* Text */
  --color-ink: #161616;            /* Headlines, emphasized body */
  --color-ink-muted: #525252;      /* Secondary type */
  --color-ink-subtle: #8c8c8c;     /* Tertiary, disabled, captions */
  --color-inverse-ink: #ffffff;     /* White on charcoal */
  --color-inverse-ink-muted: #c6c6c6;/* Light gray on charcoal */

  /* Semantic */
  --color-success: #24a148;        /* Carbon green-50 */
  --color-warning: #f1c21b;        /* Carbon yellow-30 */
  --color-error: #da1e28;          /* Carbon red-60 */
  --color-info: #0f62fe;           /* Identical to primary */

  /* Defect Colors (Dynamic dari backend SAM3, mock untuk sekarang) */
  --defect-scratch: #f1c21b;       /* Yellow */
  --defect-porosity: #fa4d56;      /* Red-pink */
  --defect-spatter: #4589ff;       /* Light blue */
  --defect-color: #ff832b;         /* Orange */
}
```

### Dark Mode (Carbon Gray-100 Theme)

```css
:root[data-theme="dark"] {
  /* Brand & Accent */
  --color-primary: #4589ff;        /* Blue 40 (brighter for dark) */
  --color-primary-hover: #0f62fe;
  --color-primary-pressed: #0066ff;
  --color-on-primary: #ffffff;

  /* Surfaces */
  --color-canvas: #161616;         /* Gray 100 */
  --color-surface-1: #262626;      /* Gray 90 */
  --color-surface-2: #393939;      /* Gray 80 */
  --color-hairline: #393939;       /* Gray 80 borders */
  --color-hairline-strong: #ffffff;/* White underline on focus */

  /* Inverse (Footer) */
  --color-inverse-canvas: #f4f4f4;
  --color-inverse-surface-1: #e0e0e0;

  /* Text */
  --color-ink: #f4f4f4;            /* Gray 20 */
  --color-ink-muted: #c6c6c6;      /* Gray 30 */
  --color-ink-subtle: #8d8d8d;     /* Gray 50 */
  --color-inverse-ink: #161616;
  --color-inverse-ink-muted: #525252;

  /* Semantic */
  --color-success: #42be65;        /* Green 40 */
  --color-warning: #f1c21b;
  --color-error: #fa4d56;          /* Red 50 */
  --color-info: #4589ff;

  /* Defect Colors (slightly brighter for dark bg) */
  --defect-scratch: #f1c21b;
  --defect-porosity: #fa4d56;
  --defect-spatter: #4589ff;
  --defect-color: #ff832b;
}
```

### Legacy Aliases (untuk komponen yang sudah ada)

```css
:root {
  --bg-app: var(--color-canvas);
  --bg-panel: var(--color-canvas);
  --bg-canvas: var(--color-surface-1);
  --bg-hover: var(--color-surface-1);
  --border-subtle: var(--color-hairline);
  --border-focus: var(--color-primary);
  --text-primary: var(--color-ink);
  --text-secondary: var(--color-ink-muted);
  --text-muted: var(--color-ink-subtle);
  --accent-primary: var(--color-primary);
  --accent-secondary: var(--color-ink);
  --status-error: var(--color-error);
  --status-success: var(--color-success);
}
```

## 4. Layout Tokens (Spacing & Radius)

*   **Border Radius**:
    *   Default (buttons, cards, inputs, containers): `0px`
    *   Badges (rare exception): `2px`
    *   Dropdown menus: `4px`
*   **Spacing** (Carbon 4px grid):
    *   `4px` / `8px` / `12px` / `16px` / `24px` / `32px` / `48px` / `96px`
    *   Button padding: `12px 16px`
    *   Form input padding: `11px 16px`
    *   Card padding: `24px` (feature), `32px` (product), `48px` (hero)
*   **Sidebar width**: Kiri `280px`, Kanan `320px`. Tengah (Canvas) bersifat `flex: 1`.

## 5. Elevation & Depth

| Level | Treatment | Use |
|---|---|---|
| 0 (flat) | No shadow, no border | Body type, hero text |
| 1 (hairline) | 1px `--color-hairline` border | Feature cards, inputs, list items |
| 2 (surface lift) | `--color-surface-1` background | Alternate-row banners, hovered cards |
| 3 (focus ring) | 2px `--color-primary` outline | Focused input, focused button |

## 6. UI Components

### 6.1. Buttons
*   **Primary**: Background `--color-primary`, text `--color-on-primary`, padding `12px 16px`, radius `0px`.
*   **Secondary**: Background `--color-ink`, text `--color-inverse-ink`.
*   **Tertiary**: Background `--color-canvas`, text `--color-primary`, border `1px --color-primary`.
*   **Ghost**: Background transparent, text `--color-primary`, no border until hover.

### 6.2. File/Batch List Item (Sidebar Kiri)
*   **Normal**: Background transparent, text `--color-ink-muted`.
*   **Hover**: Background `--color-surface-1`.
*   **Active**: Background `--color-surface-1`, border kiri `3px solid --color-primary`, text `--color-ink`.
*   **Defect Indicator**: Dot 8px, `--color-error` (defect) atau `--color-success` (clean).

### 6.3. SAM3 Canvas (Area Tengah)
*   Gambar: `object-fit: contain`, no distortion.
*   SVG overlay: `position: absolute, inset: 0`.
*   Polygon/bbox: `stroke-width: 2px`, fill opacity `15%` (normal), `40%` (hovered).

### 6.4. Inputs (Carbon signature)
*   Background `--color-surface-1`, text `--color-ink`, padding `11px 16px`, radius `0px`.
*   Focus: bottom border `2px solid --color-primary` (Carbon's signature focus treatment).

## 7. Do's and Don'ts

### Do
*   Use `0px` border-radius on every CTA, card, input, and container.
*   Pair Plex Sans weight 300 for display (42px+) with weight 400 for body.
*   Reserve IBM Blue for primary CTAs, links, focus underlines, and CTA banner.
*   Apply `letter-spacing: 0.16px` to body sizes.
*   Use surface change and 1px hairlines for card hierarchy.

### Don't
*   Don't round corners on buttons, cards, or inputs.
*   Don't bold display headlines. Weight 300 is the brand voice.
*   Don't add atmospheric depth (gradient backdrops, drop shadows).
*   Don't introduce a second brand color outside semantic status colors.
*   Don't use pill-shaped buttons.

## 8. Implementation Rules untuk Agent

*   Jangan gunakan library UI berat seperti Vuetify, Element UI, atau Tailwind. Gunakan murni Vanilla CSS dengan `var(--variable)` di atas.
*   Selalu berikan kelas semantik pada elemen (misal: `.batch-list`, `.canvas-wrapper`).
*   Pisahkan CSS di file `src/style.css` agar `App.vue` tetap bersih dari style berlebih, atau gunakan `<style scoped>` dengan import variabel.
*   Theme toggle diatur via `data-theme` attribute di `<html>`, composable `useTheme.js`, persist di `localStorage`.
