from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Snippet:
    title: str
    language: str
    code: str
    id: Optional[int] = None
    tags: str = ""          # comma-separated
    description: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
