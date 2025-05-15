from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database.config import get_db
from backend.models.order import Order, OrderStatus
from backend.models.user import User
from backend.schemas.order import OrderCreate, OrderResponse, OrderUpdate
from backend.core.security import get_current_user
from backend.models.pastry import Pastry

router = APIRouter()

@router.post("/orders/", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if all pastries exist and have sufficient quantity
    for item in order.items:
        pastry = db.query(Pastry).filter(Pastry.id == item.pastry_id).first()
        if not pastry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pastry with id {item.pastry_id} not found"
            )
        if pastry.quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient quantity for pastry {pastry.name}"
            )

    # Create new order
    db_order = Order(
        user_id=current_user.id,
        address=order.address,
        phone_number=order.phone_number,
        items=[{"pastry_id": item.pastry_id, "quantity": item.quantity} for item in order.items]
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@router.get("/orders/", response_model=List[OrderResponse])
async def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.is_admin:
        return db.query(Order).all()
    return db.query(Order).filter(Order.user_id == current_user.id).all()

@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    if not current_user.is_admin and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this order"
        )
    return order

@router.patch("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update orders"
        )

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # If order is being accepted, update pastry quantities
    if order_update.status == OrderStatus.ACCEPTED and order.status == OrderStatus.PENDING:
        for item in order.items:
            pastry = db.query(Pastry).filter(Pastry.id == item["pastry_id"]).first()
            if pastry.quantity < item["quantity"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient quantity for pastry {pastry.name}"
                )
            pastry.quantity -= item["quantity"]

    order.status = order_update.status
    order.admin_message = order_update.admin_message
    db.commit()
    db.refresh(order)
    return order 