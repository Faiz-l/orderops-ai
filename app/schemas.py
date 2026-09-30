from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models import OrderStatus

class OrderCreateSchema(BaseModel):
    id: str
    customer_email: EmailStr
    product_id: str
    quantity: int = 1
    total_amount: float
    risk_score: float = 0.0

class OrderResponseSchema(BaseModel):
    order_id: str
    status: OrderStatus
    negotiation_message: Optional[str] = None

class CustomerResponseSchema(BaseModel):
    order_id: str
    accepted: bool