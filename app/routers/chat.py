from fastapi import APIRouter, HTTPException, Depends

router = APIRouter()

@router.get("/chat")
def get_response():
    pass