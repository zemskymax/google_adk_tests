from pydantic import BaseModel, Field
from typing import List, Optional

class MainCourseItem(BaseModel):
    """Represents a main course item in the order."""
    name: str
    with_rice: Optional[str] = None # e.g., "Steamed Rice", "Fried Rice"
    price: float = 0.0

class Order(BaseModel):
    """Represents an order at the Chinese Restaurant."""
    customer_name: Optional[str] = None
    delivery_address: Optional[str] = None
    phone_number: Optional[str] = None
    is_delivery: bool = False

    appetizers: List[str] = Field(default_factory=list)
    main_courses: List[MainCourseItem] = Field(default_factory=list)
    soups: List[str] = Field(default_factory=list)
    drinks: List[str] = Field(default_factory=list)

    special_requests: Optional[str] = None

    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0

    payment_status: str = "pending"
    order_status: str = "draft"
    