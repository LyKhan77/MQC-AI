# Product Requirements Document (PRD)
**Project Name**: MQC-AI (Manufacturing Quality Control AI)
**Version**: 1.1.0 (Update: Live Inference Integration)
**Date**: 25 June 2026

## 1. Executive Summary
MQC-AI adalah sistem inspeksi kualitas berbasis Computer Vision end-to-end yang mengotomatisasi deteksi cacat pada produk industri (seperti pelapisan/coating dan pengelasan). Sistem ini terbagi menjadi dua pilar utama yang dihubungkan ke dalam **satu Dashboard terpusat**:
1. **Edge Detection Application**: Aplikasi di Jetson Nano yang memotret produk, melakukan *Live Inference Object Detection*, dan memotong (crop) area yang relevan.
2. **QC SAM3 Server**: Server berat yang memvalidasi hasil segmentasi cacat menggunakan model SAM3 secara *batch asynchronous*.

## 2. Target Pengguna (Personas)
*   **Operator Mesin/Teknisi**: Bertugas memonitor kelancaran kamera dan deteksi *live* di lini produksi.
*   **QC Inspector**: Bertugas me-review foto-foto yang telah ditangkap, memeriksa tipe cacat dengan bantuan SAM3, dan mengunduh laporan.

## 3. Scope & Features

### 3.1. Edge Detection App (Aplikasi 1 - Jetson Nano)
*   **Hardware**: Jetson Nano.
*   **Core Feature**: 
    *   Mengambil gambar dari kamera eksternal dan menjalankan *Live Object Detection* (YOLO).
    *   **Live Stream Server**: Menyediakan endpoint (WebRTC / MJPEG / WebSocket) untuk menyiarkan video langsung beserta *bounding box* pendeteksian ke Dashboard.
    *   Memotong (crop) objek dan menyimpannya ke *Shared Folder* secara terstruktur.

### 3.2. QC SAM3 Server (Aplikasi 2 - Server Backend)
*   **Hardware**: PC Server Desktop dengan GPU Mumpuni.
*   **Core Feature**:
    *   Menerima request *Asynchronous Batch Processing* dari Frontend.
    *   Menjalankan SAM3 pada folder batch untuk mencari *polygon mask* cacat.
    *   Menyimpan meta-data hasil analisis di file JSON.

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
*   **Edge App**: Python, TensorRT, OpenCV, Flask/FastAPI (untuk MJPEG/WebSocket Stream).
*   **Backend Server**: Python, FastAPI, PyTorch, Segment Anything Model (SAM3).
*   **Frontend UI**: Vite, Vue 3, Vue Router (untuk navigasi antar Menu), Vanilla CSS.

## 5. Non-Functional Requirements
*   **Latency**: Live Stream dari Jetson ke Dashboard harus berada di bawah < 500ms agar teknisi melihat *real-time*.
*   **Decoupled Services**: Kerusakan atau *offline*-nya Server SAM3 tidak boleh menghentikan fitur *Live Monitor* dari Jetson, begitu pula sebaliknya.
