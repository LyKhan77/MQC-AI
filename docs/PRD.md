# Product Requirements Document (PRD)
**Project Name**: MQC-AI (Manufacturing Quality Control AI)
**Version**: 1.2.0 (Update: Flow clarification — Edge counting gate & pluggable QC defect strategy)
**Date**: 26 June 2026

## 1. Executive Summary
MQC-AI adalah sistem inspeksi kualitas berbasis Computer Vision end-to-end yang mengotomatisasi deteksi cacat pada produk industri (seperti pelapisan/coating dan pengelasan). Sistem ini terbagi menjadi dua pilar utama yang dihubungkan ke dalam **satu Dashboard terpusat**:
1. **Edge Detection Application**: Aplikasi di Jetson Nano yang melakukan *Live Inference* untuk **deteksi & penghitungan objek produk** (bukan cacat), memotong (crop) tiap objek, dan menyediakan **gate inspeksi count** (teknisi memverifikasi jumlah benar sebelum dikirim ke QC).
2. **QC SAM3 Server**: Server berat yang men-segmentasi **cacat** pada crop secara *batch asynchronous*. Strategi deteksi cacat bersifat **pluggable** (dipilih dari Settings): mulai dari `mock`, lalu SAM3 *promptable concept segmentation* (zero-training), dengan slot untuk *detector+refine* dan *anomaly detection* di masa depan.

> **Catatan flow (v1.2.0)**: Tanggung jawab terklarifikasi — Edge mendeteksi & menghitung **objek produk** lalu crop; QC SAM3 men-segmentasi **cacat** pada crop tersebut. SAM3 tidak melakukan klasifikasi terlatih; tipe cacat ditentukan via daftar `defect_classes` yang dapat dikonfigurasi.

## 2. Target Pengguna (Personas)
*   **Operator Mesin/Teknisi**: Bertugas memonitor kelancaran kamera dan deteksi *live* di lini produksi.
*   **QC Inspector**: Bertugas me-review foto-foto yang telah ditangkap, memeriksa tipe cacat dengan bantuan SAM3, dan mengunduh laporan.

## 3. Scope & Features

### 3.1. Edge Detection App (Aplikasi 1 - Jetson Nano)
*   **Hardware**: Jetson Nano.
*   **Model**: Bobot lokal `.pt` yang sudah dilatih (mendukung model **Detection maupun Segmentation**).
*   **Core Feature**:
    *   Menjalankan *Live Inference* untuk **deteksi & penghitungan objek produk** (mis. metal sheet) dari kamera.
    *   **Object Counting** (disarankan memakai [roboflow/supervision](https://github.com/roboflow/supervision)) dengan dua mode yang dapat dikonfigurasi per-kamera:
        *   `tracking` — conveyor/stream kontinu: `ByteTrack` + `LineZone`/`PolygonZone` agar tiap objek dihitung **sekali**.
        *   `single` — stasiun 1-frame-1-objek (mis. metal sheet): single-instance per frame (`max_det=1`/top-confidence + NMS + gating area).
    *   Memotong (crop) tiap objek (dari bbox atau mask) dan menyimpannya ke *Shared Folder* secara terstruktur.
    *   **Count Inspection Gate**: teknisi memverifikasi jumlah hitungan benar; setelah **approve**, trigger pengiriman folder crop ke QC.
    *   **Live Stream Server**: endpoint (WebRTC / MJPEG / WebSocket) untuk menyiarkan video + *bounding box* ke Dashboard.

### 3.2. QC SAM3 Server (Aplikasi 2 - Server Backend)
*   **Hardware**: PC Server Desktop dengan GPU Mumpuni.
*   **Core Feature**:
    *   Menerima request *Asynchronous Batch Processing* (**polling**: submit → `job_id` → poll status) dari Frontend, atas **folder berisi crop** dari Edge.
    *   Menjalankan **pipeline deteksi cacat pluggable** (dipilih dari Settings) untuk menghasilkan *polygon* cacat atas daftar `defect_classes`:
        *   `mock` (polygon dummy, untuk membangun sistem end-to-end),
        *   `sam3_prompt` (SAM3 *promptable concept segmentation*, zero-training),
        *   slot masa depan: `detector_refine` (YOLO defect + SAM3 perhalus mask), `anomaly` (anomalib/PatchCore dari sampel bagus).
    *   Persistensi metadata di **SQLite** + hasil/JSON & gambar di **filesystem/NAS**.

### 3.3. UI Dashboard (Satu Portal, Dua Fungsi)
Menggunakan tema *GSPE Corporate Dark Theme* (Navy Blue & Bright Blue).
*   **Menu 1: Live Edge Monitor (Untuk Teknisi)**
    *   Menampilkan *Live Video Feed* langsung dari Jetson Nano (Aplikasi 1).
    *   Overlay *real-time* bounding box pendeteksian objek di mesin produksi.
    *   Indikator status koneksi Jetson Nano (Online/Offline, FPS, Suhu).
*   **Menu 2: QC Inspector Studio (Untuk Tim QC)**
    *   *Studio Layout (3 Kolom)*: Batch Manager (Kiri), Inspection Canvas (Tengah), Defect Details & Export (Kanan).
    *   Membaca hasil foto dari *Shared Folder*, mengirim ke Server SAM3, dan me-render anotasi cacat.
    *   Fungsi Export Crop & Full Frame.

## 4. Arsitektur Teknis
*   **Edge App**: Python, TensorRT/Ultralytics, OpenCV, `supervision` (counting/tracking), Flask/FastAPI (untuk MJPEG/WebSocket Stream).
*   **Backend Server**: Python, FastAPI, SQLAlchemy + **SQLite**, PyTorch, Segment Anything Model (SAM3). Async via **polling**.
*   **Frontend UI**: Vite, Vue 3, Vue Router (untuk navigasi antar Menu), Vanilla CSS.
*   **Build order**: `qc_server` lebih dulu (dapat dites tanpa hardware), lalu `edge_app`. Detail rencana: `docs/superpowers/plans/qc-server-plan.md`.

## 5. Non-Functional Requirements
*   **Latency**: Live Stream dari Jetson ke Dashboard harus berada di bawah < 500ms agar teknisi melihat *real-time*.
*   **Decoupled Services**: Kerusakan atau *offline*-nya Server SAM3 tidak boleh menghentikan fitur *Live Monitor* dari Jetson, begitu pula sebaliknya.
*   **Single-user (MVP)**: Autentikasi/role ditunda; reviewer berasal dari konfigurasi.
*   **Configurable defect strategy**: Pemilihan strategi deteksi cacat & daftar `defect_classes` dapat diubah dari Settings tanpa mengubah API/Frontend.
