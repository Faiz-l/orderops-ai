from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Order, OrderStatus, Negotiation
from app.schemas import OrderCreateSchema, CustomerResponseSchema, OrderResponseSchema
from app.agent import order_workflow, OrderAgentState

router = APIRouter()

@router.post("/seed-products")
def seed_products(db: Session = Depends(get_db)):
    db.query(Product).delete()
    db.add_all([
        Product(id="P101", name="Wireless Mouse", price=25.0, stock_quantity=0),
        Product(id="P102", name="Ergonomic Mouse", price=30.0, stock_quantity=10),
        Product(id="P103", name="Mechanical Keyboard", price=80.0, stock_quantity=5),
    ])
    db.commit()
    return {"message": "Sample products created successfully"}

@router.post("/orders", response_model=OrderResponseSchema)
def create_order(payload: OrderCreateSchema, db: Session = Depends(get_db)):
    new_order = Order(
        id=payload.id,
        customer_email=payload.customer_email,
        product_id=payload.product_id,
        quantity=payload.quantity,
        total_amount=payload.total_amount,
        risk_score=payload.risk_score,
        status=OrderStatus.PENDING
    )
    db.add(new_order)
    db.commit()

    initial_state: OrderAgentState = {
        "order_id": payload.id,
        "customer_email": payload.customer_email,
        "product_id": payload.product_id,
        "quantity": payload.quantity,
        "risk_score": payload.risk_score,
        "status": OrderStatus.PENDING.value,
        "proposed_product_id": None,
        "negotiation_message": None
    }

    final_state = order_workflow.invoke(initial_state)

    new_order.status = OrderStatus(final_state["status"])
    db.commit()

    return OrderResponseSchema(
        order_id=payload.id,
        status=final_state["status"],
        negotiation_message=final_state.get("negotiation_message")
    )

@router.post("/orders/respond")
def respond_to_offer(payload: CustomerResponseSchema, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    negotiation = db.query(Negotiation).filter(Negotiation.order_id == payload.order_id).first()

    if payload.accepted and negotiation:
        order.product_id = negotiation.proposed_product_id
        order.status = OrderStatus.FULFILLED
        negotiation.status = "ACCEPTED"
    else:
        order.status = OrderStatus.CANCELLED
        if negotiation:
            negotiation.status = "REJECTED"

    db.commit()
    return {"order_id": order.id, "final_status": order.status}