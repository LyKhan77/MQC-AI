# MQC-AI Dashboard Design System

Sistem desain ini sangat terinspirasi dari gaya **Linear / Vercel (High-Tech Minimalist)** dari katalog *getdesign.md*. Pendekatan *dark mode* dengan kontras tinggi ini dipilih secara spesifik agar warna-warni anotasi *bounding box* dan poligon SAM3 sangat menonjol di atas gambar produk, tanpa membuat mata lelah saat inspeksi berjam-jam.

## 1. Core Principles
*   **Dark Mode First**: UI dominan gelap untuk menonjolkan area gambar (canvas) dan mengurangi kelelahan mata Inspektor.
*   **High-Contrast Data**: Teks data (jumlah cacat, koordinat) menggunakan warna kontras terang atau monospace agar sangat mudah dibaca (scannable).
*   **Subtle Borders**: Memisahkan area layout (Sidebar, Canvas, Detail) menggunakan garis 1px yang sangat tipis (border solid), tanpa bayangan (shadow) berlebihan.
*   **Vibrant Accents for Defects**: Warna terang/neon *hanya* digunakan untuk status (Merah = Defect) dan anotasi (Garis SAM3).

## 2. Typography
Gunakan font modern *sans-serif* yang sangat bersih, dan *monospace* untuk angka/data.
*   **Primary Font**: `Inter`, `Geist`, atau sistem sans-serif (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto...`).
*   **Mono Font**: `JetBrains Mono`, `Geist Mono`, atau sistem monospace. Digunakan untuk *file path*, persentase akurasi, dan jumlah cacat.

## 3. Color Tokens (CSS Variables)
Konvensi warna yang harus digunakan dalam proyek Vanilla CSS / Vue:

```css
:root {
  /* Backgrounds (GSPE Corporate Dark Theme) */
  --bg-app: #031124;         /* Very dark navy (Background paling belakang) */
  --bg-panel: #06244A;       /* GSPE Dark Navy Blue (Sidebar kiri dan kanan) */
  --bg-canvas: #020A16;      /* Super dark navy / almost black (Area gambar tengah) */
  --bg-hover: #2B5672;       /* GSPE Muted Steel Blue (Hover effect) */

  /* Borders */
  --border-subtle: #116DFF;  /* GSPE Bright Blue dengan opacity (akan di-handle di CSS) */
  --border-focus: #C6A105;   /* GSPE Gold (Border elemen aktif) */

  /* Text Colors */
  --text-primary: #FFFFFF;   /* Teks utama (judul, data penting) */
  --text-secondary: #A0C0DF; /* Teks deskripsi bernuansa biru muda */
  --text-muted: #557799;     /* Teks non-aktif atau disable */

  /* Accent & Status Colors (Sangat Vibrant) */
  --accent-primary: #116DFF; /* GSPE Bright Blue (Tombol utama) */
  --accent-secondary: #C6A105; /* GSPE Gold (Aksen sekunder) */
  --status-error: #F85149;   /* Merah cerah untuk indikator barang Cacat (Defect) */
  --status-success: #238636; /* Hijau cerah untuk barang OK/Bersih */

  /* Defect Colors (Untuk Bounding Box SAM3) */
  --defect-scratch: #FFD700;   /* Kuning untuk Goresan */
  --defect-porosity: #FF24BD;  /* Pink cerah untuk Porosity */
  --defect-spatter: #00E5FF;   /* Cyan untuk Spatter */
  --defect-color: #FFA500;     /* Orange untuk Warna tak sesuai */
}
```

## 4. Layout Tokens (Spacing & Radius)
*   **Radius**: Karena ini aplikasi produktivitas bergaya *high-tech*, *border-radius* dibuat kecil (tajam) atau moderat.
    *   Panels / Containers: `6px`
    *   Buttons: `4px`
*   **Spacing**: Sangat padat (dense) untuk menampilkan sebanyak mungkin daftar batch di kolom kiri, tetapi cukup lega di kolom kanan (Detail Cacat).
    *   Sidebar width: Kiri `280px`, Kanan `320px`. Tengah (*Canvas*) bersifat `flex: 1`.

## 5. UI Components

### 5.1. File/Batch List Item (Sidebar Kiri)
Item daftar gambar harus *compact*.
*   **Normal State**: Background transparan, teks abu-abu (`--text-secondary`).
*   **Hover State**: Background `--bg-hover`, cursor pointer.
*   **Active State**: Background `--bg-hover`, border kiri tebal dengan `--accent-primary`, teks putih (`--text-primary`).
*   **Indikator Cacat**: Titik kecil berukuran 8px (dot) berwarna merah (`--status-error`) jika terdeteksi cacat, atau hijau (`--status-success`) jika bersih.

### 5.2. Action Buttons (Sidebar Kanan)
*   **Primary Action (Export Crop)**: Background `--text-primary`, teks `--bg-app` (Gaya tombol *inverse* Vercel).
*   **Secondary Action (Export Full)**: Background transparan, border `--border-focus`, teks `--text-primary`.

### 5.3. SAM3 Canvas (Area Tengah)
*   Gambar produk tidak boleh terdistorsi (`object-fit: contain`).
*   Kanvas SVG atau overlay HTML absolute harus tepat berada di atas gambar.
*   Garis *polygon* atau *bounding box* menggunakan ketebalan `2px` dengan warna dari *Defect Colors*, dan fill (area dalam) transparan dengan opacity `15%`.
*   Saat list cacat di sebelah kanan di-*hover*, opacity fill pada bounding box terkait di kanvas naik menjadi `40%`.

## 6. Implementation Rules untuk Agent
*   Jangan gunakan library UI berat seperti Vuetify, Element UI, atau Tailwind. Gunakan murni Vanilla CSS dengan `var(--variable)` di atas.
*   Selalu berikan kelas semantik pada elemen (misal: `.batch-list`, `.canvas-wrapper`).
*   Pisahkan CSS di file `src/assets/style.css` agar `App.vue` tetap bersih dari style berlebih, atau gunakan `<style scoped>` dengan import variabel.
