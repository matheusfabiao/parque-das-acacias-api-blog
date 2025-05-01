import logging
from http import HTTPStatus

import httpx
from fastapi import HTTPException

from src.core.config import settings
from src.core.security import get_headers
from src.utils.html import clean_html  # moveremos isso também!
from src.models.schemas import PostResponse

logger = logging.getLogger(__name__)
WP_URL = settings.WP_URL
WP_LOGIN = settings.WP_LOGIN
WP_PASSWORD = settings.WP_PASSWORD

async def get_jwt_token_from_wp() -> str:
    logger.info("Obtendo token JWT da API WordPress")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{WP_URL}/wp-json/jwt-auth/v1/token",
                json={"username": WP_LOGIN, "password": WP_PASSWORD},
            )
            response.raise_for_status()
            return response.json()["token"]
        except httpx.HTTPError as e:
            logger.error(f"Erro ao obter token JWT: {e}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Erro ao obter token JWT: {e}",
            )

async def get_media_url(post_data, client, token):
    logger.info(f"Buscando mídia para o post ID: {post_data['id']}")
    media_response = await client.get(
        f"{WP_URL}/wp-json/wp/v2/media/{post_data['featured_media']}",
        headers=get_headers(token),
        params={"_fields": "guid.rendered"},
    )
    if media_response.status_code == HTTPStatus.OK:
        post_data["featured_media"] = media_response.json().get("guid", {}).get("rendered")
    else:
        post_data["featured_media"] = None
        logger.warning(f"Mídia não encontrada para post ID: {post_data['id']}")
    return post_data

async def fetch_wp_data(token: str):
    logger.info("Buscando posts no WordPress")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WP_URL}/wp-json/wp/v2/posts",
                headers=get_headers(token),
                params={
                    "per_page": 3,
                    "_fields": "id,link,title,excerpt,featured_media",
                },
            )
            response.raise_for_status()
            posts = response.json()
            formatted_posts = []

            for post in posts:
                clean_excerpt = clean_html(post["excerpt"]["rendered"])
                post_data = {
                    "id": post["id"],
                    "link": post["link"],
                    "title": post["title"],
                    "excerpt": clean_excerpt,
                    "featured_media": post["featured_media"],
                }

                if post_data["featured_media"]:
                    post_data = await get_media_url(post_data, client, token)

                formatted_posts.append(post_data)

            return formatted_posts
    except httpx.HTTPError as e:
        logger.error(f"Erro ao buscar dados da API WordPress: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar dados da API WordPress: {e}",
        )
