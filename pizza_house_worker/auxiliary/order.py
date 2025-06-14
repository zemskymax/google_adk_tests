from pydantic import BaseModel, Field
from typing import List, Optional


class PizzaItem(BaseModel):
    """Represents a pizza item in the order."""
    size: str
    crust: str
    toppings: List[str] = Field(default_factory=list)
    price: float = 0.0

class Order(BaseModel):
    """Represents an order at Luigi's Pizza House."""
    customer_name: Optional[str] = None
    delivery_address: Optional[str] = None
    phone_number: Optional[str] = None
    is_delivery: bool = False

    pizzas: List[PizzaItem] = Field(default_factory=list)
    sides: List[str] = Field(default_factory=list)
    drinks: List[str] = Field(default_factory=list)
    combos: List[str] = Field(default_factory=list)

    special_requests: Optional[str] = None

    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0

    payment_status: str = "pending"
    order_status: str = "draft"
