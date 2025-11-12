"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model corresponds to a MongoDB collection. The collection
name is the lowercase of the class name by convention.

Example: class BlogPost -> collection "blogpost"
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

# Auth/User
class AdminUser(BaseModel):
    email: str = Field(..., description="Admin email (unique)")
    password_hash: str = Field(..., description="BCrypt hash of password")
    role: str = Field("admin", description="Role: admin|editor|viewer")
    name: Optional[str] = Field(None, description="Display name")
    last_login: Optional[datetime] = Field(None)
    is_active: bool = Field(True)

# Blog
class BlogPost(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str = Field(..., description="Rich text (HTML or JSON)")
    featured_image: Optional[str] = Field(None, description="URL to hero image")
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    status: str = Field("draft", description="draft|published")
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    published_at: Optional[datetime] = None

# Partner logos
class PartnerLogo(BaseModel):
    name: str
    image_url: str
    alt: str
    link: Optional[str] = None
    order: int = 0
    is_active: bool = True

# Case studies
class CaseStudy(BaseModel):
    title: str
    slug: str
    client: str
    project_date: Optional[datetime] = None
    description: Optional[str] = None
    featured_image: Optional[str] = None
    content: Optional[str] = Field(None, description="Rich text body")
    tags: List[str] = Field(default_factory=list)
    gallery: List[str] = Field(default_factory=list, description="List of image URLs")
    status: str = Field("draft", description="draft|published")
