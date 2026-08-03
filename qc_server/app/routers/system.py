from fastapi import APIRouter

from ..services.gpu import get_gpu_inventory

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/gpus")
def list_gpus():
    return get_gpu_inventory()
