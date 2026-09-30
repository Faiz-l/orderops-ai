from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

from app.config import settings
from app.database import SessionLocal
from app.models import Product, OrderStatus, Negotiation

class OrderAgentState(TypedDict):
    order_id: str
    customer_email: str
    product_id: str
    quantity: int
    risk_score: float
    status: str
    proposed_product_id: Optional[str]
    negotiation_message: Optional[str]

def check_fraud_node(state: OrderAgentState) -> OrderAgentState:
    if state["risk_score"] >= settings.FRAUD_THRESHOLD:
        state["status"] = OrderStatus.FLAGGED_FRAUD.value
    else:
        state["status"] = OrderStatus.PROCESSING.value
    return state

def check_inventory_node(state: OrderAgentState) -> OrderAgentState:
    db = SessionLocal()
    product = db.query(Product).filter(Product.id == state["product_id"]).first()
    
    if product and product.stock_quantity >= state["quantity"]:
        product.stock_quantity -= state["quantity"]
        db.commit()
        state["status"] = OrderStatus.FULFILLED.value
    else:
        state["status"] = OrderStatus.NEGOTIATING.value
    db.close()
    return state

def generate_negotiation_node(state: OrderAgentState) -> OrderAgentState:
    db = SessionLocal()
    alt_product = db.query(Product).filter(Product.stock_quantity > 0).first()
    
    if not alt_product:
        state["status"] = OrderStatus.CANCELLED.value
        db.close()
        return state

    state["proposed_product_id"] = alt_product.id
    discount = 10.0

    if settings.GEMINI_API_KEY:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=settings.GEMINI_API_KEY)
            prompt = PromptTemplate(
                input_variables=["alt_name", "discount"],
                template="Write a polite concise email offering alternative product {alt_name} with a {discount}% discount because original order is out of stock."
            )
            chain = prompt | llm
            res = chain.invoke({"alt_name": alt_product.name, "discount": discount})
            state["negotiation_message"] = res.content
        except Exception:
            state["negotiation_message"] = f"Original item out of stock. Would you accept {alt_product.name} with {discount}% off?"
    else:
        state["negotiation_message"] = f"Original item out of stock. Would you accept {alt_product.name} with {discount}% off?"

    negotiation = Negotiation(
        id=f"neg_{state['order_id']}",
        order_id=state['order_id'],
        proposed_product_id=alt_product.id,
        offered_discount_pct=discount,
        message_text=state["negotiation_message"]
    )
    db.add(negotiation)
    db.commit()
    db.close()
    return state

def route_after_fraud(state: OrderAgentState) -> str:
    if state["status"] == OrderStatus.FLAGGED_FRAUD.value:
        return END
    return "check_inventory"

def route_after_inventory(state: OrderAgentState) -> str:
    if state["status"] == OrderStatus.FULFILLED.value:
        return END
    return "generate_negotiation"

# Graph Build
builder = StateGraph(OrderAgentState)
builder.add_node("check_fraud", check_fraud_node)
builder.add_node("check_inventory", check_inventory_node)
builder.add_node("generate_negotiation", generate_negotiation_node)

builder.set_entry_point("check_fraud")
builder.add_conditional_edges("check_fraud", route_after_fraud)
builder.add_conditional_edges("check_inventory", route_after_inventory)
builder.add_edge("generate_negotiation", END)

order_workflow = builder.compile()