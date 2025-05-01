import logging
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from http import HTTPStatus

from src.core.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    logger.info("Verificando token JWT")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.WP_JWT_SECRET_KEY,
            algorithms=["HS256"],
        )
        logger.info("Token JWT válido")
        return {"token": credentials.credentials, "payload": payload}
    except JWTError as e:
        logger.error(f"Erro na verificação do token JWT: {e}")
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=f"Erro na verificação do token JWT: {e}",
        )

def get_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
