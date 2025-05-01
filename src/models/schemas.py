from typing import Dict, Optional
from pydantic import BaseModel, HttpUrl

class PostResponse(BaseModel):
    id: int
    link: HttpUrl
    title: Dict[str, str]
    excerpt: str
    featured_media: Optional[HttpUrl] = None
