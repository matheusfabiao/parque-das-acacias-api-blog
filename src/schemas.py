from typing import Dict, Optional

from pydantic import BaseModel, HttpUrl


class PostResponse(BaseModel):
    """
    Schema para representar uma resposta de postagem.

    Args:
        BaseModel (pydantic.BaseModel):
            classe base para criar schemas.

    Attributes:
        id (int):
            ID do post.
        link (HttpUrl):
            URL do post.
        title (Dict[str, str]):
            Título do post.
        excerpt (str):
            Resumo do post.
        featured_media (Optional[HttpUrl]):
            URL da imagem destacada do post.
    """

    id: int
    link: HttpUrl
    title: Dict[str, str]   # {'rendered': 'Título do post'}
    excerpt: str
    featured_media: Optional[HttpUrl] = None  # URL ou None
