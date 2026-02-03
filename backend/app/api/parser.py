from fastapi import APIRouter

router = APIRouter()

@router.get("/parser/status")
async def parser_status():
    return {"status": "placeholder"}
