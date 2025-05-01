from fastapi import APIRouter, Depends

from src.models.schemas import PostResponse
from src.services.wordpress import fetch_wp_data, get_jwt_token_from_wp
from src.core.security import verify_token

router = APIRouter()

@router.get("/posts", response_model=list[PostResponse])
async def get_posts(auth_data: dict = Depends(verify_token)):
    token = auth_data["token"]
    return await fetch_wp_data(token)

@router.post("/auth")
async def auth():
    token = await get_jwt_token_from_wp()
    return {"token": token}
