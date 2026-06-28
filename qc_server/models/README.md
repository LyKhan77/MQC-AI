# Models

Drop your trained model weight files here (e.g. `metal_sheet.pt`).

- Supported: Ultralytics YOLO `.pt` (detection or segmentation). Other weight
  files (`.pth`, `.onnx`, `.engine`) are also git-ignored.
- Weight files are **never committed** (see root `.gitignore`); only this README
  is tracked so the folder exists.
- Select the **active model** in the dashboard: **Settings → Model Config →
  Active Model** (lists the files found in this folder).
- Path is configurable via `MQC_MODELS_DIR` (defaults to `./models`, relative to
  `qc_server/`).
