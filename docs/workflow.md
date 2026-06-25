# System Workflow & Architecture

Dokumen ini menjelaskan aliran data dari ujung kamera di pabrik hingga di-ekspor oleh QC Inspector.

## 1. Architecture Overview Diagram

```mermaid
graph TD
    subgraph Edge Environment [Pabrik / Jetson Nano]
        Kamera[Industrial Camera]
        EdgeApp[Edge App: Object Detection<br>+ Live Stream Server]
        Kamera -->|Raw Video| EdgeApp
        EdgeApp -->|Save Crop Object| SharedNAS[(Shared Storage / NAS)]
    end

    subgraph QC Office [PC Server & Browser]
        UI[QC Dashboard Frontend<br>Vue 3 SPA + Vue Router]
        SAMServer[QC SAM3 Backend<br>FastAPI + SAM3]
        
        %% Stream Live
        EdgeApp == "WebSocket / MJPEG" ==>|Menu 1: Live Monitor| UI
        
        %% Analisis QC
        SharedNAS -.->|Inspector Membuka Folder| UI
        UI -->|Kirim path folder batch| SAMServer
        SAMServer -->|Batch Processing| SAMServer
        SAMServer ==>|Menu 2: Data JSON & Masks| UI
    end
```

## 2. End-to-End Operational Workflow

Berikut adalah alur harian yang dilakukan oleh sistem dan pengguna melalui satu pintu **QC Dashboard**:

### Fase 1: Pemantauan Produksi Langsung (Menu Live Monitor)
1. User (Teknisi/Operator) membuka Dashboard, masuk ke tab **"Live Monitor"**.
2. Dashboard langsung terhubung ke IP lokal Jetson Nano.
3. User melihat video *real-time* dari mesin konveyor, beserta *bounding box* hijau yang menandakan "Objek Terdeteksi" saat barang lewat.
4. Edge App secara otomatis dan simultan memotong area dalam *bounding box* tersebut dan menyimpannya ke folder harian di NAS tanpa mengganggu siaran *live*.

### Fase 2: Inisiasi Batch Analisis Cacat (Menu QC Inspector)
1. Setelah batch jam kerja selesai (misal shift 1 usai), QC Inspector membuka Dashboard, masuk ke tab **"QC Studio"**.
2. Inspector menekan tombol **"Load Batch"** dan menunjuk folder shift 1 di NAS.
3. Dashboard meminta **QC SAM3 Server** untuk memproses *batch* tersebut. SAM3 Server mengeksekusi model segmentasi secara asinkron di belakang layar.

### Fase 3: Proses Review Cacat
1. Transisi bersifat *instan*. Di **Kolom Tengah**, gambar langsung muncul beserta *polygon mask* cacat yang sudah dihitung sebelumnya.
2. Di **Kolom Kanan**, terdapat ringkasan *Coating Defects* & *Welding Defects*.
3. Inspector me-review kesesuaian deteksi AI.

### Fase 4: Export & Reporting
1. Inspector menekan tombol **Export** di kolom kanan.
2. Sistem men-generate gambar yang sudah di-overlay warna, beserta metadata JSON (berguna jika engineer ingin melatih ulang / *retraining* model Jetson atau SAM3).
