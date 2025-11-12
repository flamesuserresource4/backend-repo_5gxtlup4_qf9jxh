from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class Lead(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    company: Optional[str] = Field(default="")
    revenue_goal: Optional[str] = Field(default="")
