from pydantic import BaseModel, Field
from typing import Optional
class ProductIn(BaseModel):
    category: Optional[str] = None
    title: str
    brand: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    discount_pct: Optional[float] = Field(default=None, description="0-100")
    rating: Optional[float] = None
    reviews: Optional[int] = None
    product_link: Optional[str] = None
    image: Optional[str] = None
    availability: Optional[str] = None
    source: Optional[str] = None
class ProductOut(ProductIn):
    id: str = Field(alias="_id")
