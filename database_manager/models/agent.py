from typing import List

from pydantic import BaseModel


class Agent(BaseModel):
    name: str
    description: str
    topics: List[str]
    output_format: str
    is_active: bool = True
