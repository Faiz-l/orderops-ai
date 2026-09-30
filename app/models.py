import enum
from sqlalchemy import Column, String, Float, Integer, Enum, Text
from app.database import Base

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    FLAGGED_FRAUD = "FLAGGED_FRAUD"
    PROCESSING = "PROCESSING"
    NEGOTIATING = "NEGOTIATING"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    customer_email = Column(String, nullable=False)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    total_amount = Column(Float, nullable=False)
    risk_score = Column(Float, default=0.0)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)

class Negotiation(Base):
    __tablename__ = "negotiations"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, nullable=False)
    proposed_product_id = Column(String, nullable=False)
    offered_discount_pct = Column(Float, default=10.0)
    message_text = Column(Text)
    status = Column(String, default="OFFER_SENT")