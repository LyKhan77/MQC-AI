import subprocess


def get_gpu_inventory():
    query = (
        "index,name,memory.total,memory.used,memory.free,utilization.gpu"
    )
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                f"--query-gpu={query}",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "gpus": [], "error": str(exc)}

    if result.returncode != 0:
        return {
            "available": False,
            "gpus": [],
            "error": result.stderr.strip() or "nvidia-smi failed",
        }

    gpus = []
    for line in result.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 6:
            continue
        try:
            utilization = 0 if parts[5].upper() == "N/A" else int(parts[5])
            gpus.append({
                "index": int(parts[0]),
                "name": parts[1],
                "memory_total_mb": int(parts[2]),
                "memory_used_mb": int(parts[3]),
                "memory_free_mb": int(parts[4]),
                "utilization_percent": utilization,
            })
        except ValueError:
            continue
    return {
        "available": bool(gpus),
        "gpus": gpus,
        "error": None if gpus else "no NVIDIA GPU detected",
    }


def validate_device(value: str, inventory=None) -> str:
    value = str(value or "auto").strip().lower()
    if value in {"auto", "cpu"}:
        return value
    if not value.isdigit():
        raise ValueError("device must be auto, cpu, or a GPU index")
    if inventory is None:
        inventory = get_gpu_inventory()
    indexes = {gpu["index"] for gpu in inventory["gpus"]}
    if int(value) not in indexes:
        raise ValueError(f"GPU index {value} is not detected")
    return value
