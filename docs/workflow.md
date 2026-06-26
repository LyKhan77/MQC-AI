# System Workflow & Architecture

Dokumen ini menjelaskan aliran data dari ujung kamera di pabrik hingga di-ekspor oleh QC Inspector.

## 1. Architecture Overview Diagram

```mermaid
graph TD
    subgraph Edge Environment [Pabrik / Jetson Nano]
        Kamera[Industrial Camera]
        EdgeApp[Edge App: Object Detection + Counting<br>Detection/Seg .pt + supervision<br>+ Live Stream Server]
        Gate{Count Inspection Gate<br>Teknisi approve hitungan}
        Kamera -->|Raw Video| EdgeApp
        EdgeApp -->|Crop tiap objek| Gate
        Gate -->|APPROVED: Save Crops| SharedNAS[(Shared Storage / NAS)]
    end

    subgraph QC Office [PC Server & Browser]
        UI[QC Dashboard Frontend<br>Vue 3 SPA + Vue Router]
        SAMServer[QC Backend<br>FastAPI + SQLite + SAM3<br>pluggable defect strategy]

        %% Stream Live
        EdgeApp == "WebSocket / MJPEG" ==>|Menu 1: Live Monitor| UI

        %% Trigger & Analisis QC
        Gate -.->|Trigger: POST /api/batches path crop| UI
        SharedNAS -.->|Folder crop| SAMServer
        UI -->|Submit batch + poll status| SAMServer
        SAMServer -->|Async batch: defect segmentation| SAMServer
        SAMServer ==>|Menu 2: Data JSON & Polygons| UI
    end
```

## 2. End-to-End Operational Workflow

Berikut adalah alur harian yang dilakukan oleh sistem dan pengguna melalui satu pintu **QC Dashboard**:

### Fase 1: Pemantauan & Penghitungan Objek (Menu Live Monitor)
1. User (Teknisi/Operator) membuka Dashboard, masuk ke tab **"Live Monitor"**.
2. Dashboard langsung terhubung ke IP lokal Jetson Nano.
3. User melihat video *real-time* beserta *bounding box*/mask deteksi **objek produk** (mis. metal sheet) dari model `.pt` terlatih.
4. Edge App **menghitung jumlah objek** memakai `supervision`:
   - mode `tracking` (conveyor): `ByteTrack` + `LineZone`/`PolygonZone` → tiap objek dihitung sekali;
   - mode `single` (stasiun, 1-frame-1-objek): single-instance per frame (`max_det=1`/top-confidence + NMS).
5. Edge App memotong (crop) tiap objek dan menyimpannya sementara.

### Fase 2: Gate Inspeksi Count & Trigger ke QC
1. Teknisi **memverifikasi** apakah jumlah hitungan sudah benar (objek terdeteksi & terhitung sesuai).
2. Setelah **approve**, crop disimpan ke folder harian di NAS dan Dashboard mengirim **trigger** `POST /api/batches` berisi path folder crop ke **QC Backend**.

### Fase 3: Inisiasi Batch Analisis Cacat (Menu QC Inspector)
1. QC Inspector membuka tab **"QC Studio"**; batch yang sudah ter-trigger tampil (atau Inspector menunjuk folder crop secara manual).
2. QC Backend memproses *batch* secara **asinkron** memakai **pipeline deteksi cacat pluggable** (dipilih dari Settings: `mock` → `sam3_prompt` → slot `detector_refine`/`anomaly`) atas daftar `defect_classes`.
3. Frontend **polling** status job sampai selesai (`done`).

### Fase 4: Proses Review Cacat
1. Setelah `done`, di **Kolom Tengah** gambar muncul beserta *polygon* cacat yang sudah dihitung.
2. Di **Kolom Kanan**, terdapat ringkasan *Coating Defects* & *Welding Defects*.
3. Inspector me-review kesesuaian deteksi AI.

### Fase 5: Export & Reporting
1. Inspector menekan tombol **Export** di kolom kanan.
2. Sistem men-generate gambar yang sudah di-overlay warna, beserta metadata JSON (berguna jika engineer ingin melatih ulang / *retraining* model Jetson atau SAM3).
