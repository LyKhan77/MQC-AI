# MQC-AI (Manufacturing Quality Control AI)

## Project Overview
MQC-AI adalah sistem inspeksi kualitas produk berbasis *Computer Vision* end-to-end yang dirancang untuk otomasi deteksi cacat di lini produksi industri (misal: pelapisan/coating dan pengelasan). Proyek ini merupakan inisiatif untuk GSPE.

## Arsitektur & Workspace (Monorepo)
Sistem ini menggunakan arsitektur *decoupled* yang dipisahkan menjadi 3 komponen utama, namun dikelola dalam satu *repository* (monorepo):

1. **`qc_frontend/` (Frontend UI Dashboard)**
   - **Fungsi**: Dashboard interaktif tunggal untuk memantau kamera produksi secara *live* dan me-review hasil inspeksi secara batch.
   - **Tech Stack**: Vue 3 (Composition API), Vite, Vue Router, Vanilla CSS (GSPE Corporate Dark Theme).
2. **`qc_server/` (Backend SAM3 Server - TBA)**
   - **Fungsi**: Menjalankan inferensi model SAM3 berat pada folder secara *asynchronous batch processing*.
   - **Tech Stack**: Python, FastAPI, PyTorch, SAM3.
3. **`edge_app/` (Jetson Nano Edge - TBA)**
   - **Fungsi**: Terhubung langsung ke kamera industri, melakukan Object Detection (YOLO), memotong objek (crop), dan memancarkan *Live Video Stream*.
   - **Tech Stack**: Python, TensorRT, OpenCV.

## Dokumentasi Teknis
Seluruh desain dan spesifikasi teknis disimpan di dalam direktori `docs/`:
- [Product Requirements Document (PRD)](./docs/PRD.md)
- [System Workflow & Architecture](./docs/workflow.md)
- [Design System & UI Tokens](./DESIGN.md)

## Implementation Plans
Rencana implementasi (*Implementation Plan*) untuk agen eksekusi disimpan di `docs/superpowers/plans/`:
- [UI Dashboard Plan](./docs/superpowers/plans/2026-06-25-qc-dashboard-ui.md) (Fokus Utama Saat Ini)

---
*Dokumen ini harus selalu diperbarui setiap kali ada penambahan fitur utama atau perubahan arsitektur.*
