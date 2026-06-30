from typing import Optional

from pydantic import BaseModel


class BlogContext(BaseModel):
    topic: str
    experience: str
    highlights: Optional[str] = None
    rating: Optional[int] = None
