"""
Database Schemas for Affiliate Site

Each Pydantic model corresponds to a MongoDB collection. The collection name is the lowercase class name.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

class Category(BaseModel):
    name: str = Field(..., description="Category name, e.g., 'Beginner Guitars'")
    slug: str = Field(..., description="URL-friendly slug, unique per category")

class AffiliateProduct(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Short description")
    price: Optional[float] = Field(None, ge=0, description="Price (optional)")
    category: str = Field(..., description="Category slug this product belongs to")
    affiliate_url: HttpUrl = Field(..., description="Affiliate tracking link")
    image_url: Optional[HttpUrl] = Field(None, description="Product image URL")
    tags: Optional[List[str]] = Field(default_factory=list, description="Searchable tags")
    featured: bool = Field(False, description="Whether to highlight on homepage")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating 0-5")

class Click(BaseModel):
    product_id: str = Field(..., description="ID string of the clicked product")
    source: Optional[str] = Field(None, description="Where the click originated (e.g., 'hero', 'grid')")
