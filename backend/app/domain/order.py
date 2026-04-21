"""Доменные сущности заказа."""

import uuid
from datetime import datetime,  timezone
from decimal import Decimal
from enum import Enum
from typing import List
from dataclasses import field, dataclass
from .exceptions import (
    OrderAlreadyPaidError,
    OrderCancelledError,
    InvalidQuantityError,
    InvalidPriceError,
    InvalidAmountError,
)


# TODO: Реализовать OrderStatus (str, Enum)
# Значения: CREATED, PAID, CANCELLED, SHIPPED, COMPLETED
class OrderStatus(str, Enum):
    CREATED = "created"  
    PAID = "paid"
    CANCELLED = "cancelled"
    SHIPPED = "shipped"
    COMPLETED = "completed"



# TODO: Реализовать OrderItem (dataclass)
# Поля: product_name, price, quantity, id, order_id
# Свойство: subtotal (price * quantity)
# Валидация: quantity > 0, price >= 0
@dataclass
class OrderItem:
    product_name: str 
    price: Decimal 
    quantity: int 
    order_id: uuid.UUID = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
   

    def __post_init__(self):
        if self.quantity <= 0: 
            raise InvalidQuantityError(self.quantity)
        if self.price < 0:
            raise InvalidPriceError(self.price)
    @property
    def subtotal(self):
        return self.price * self.quantity




# TODO: Реализовать OrderStatusChange (dataclass)
# Поля: order_id, status, changed_at, id
@dataclass
class OrderStatusChange:
    order_id: uuid.UUID
    status: OrderStatus
    changed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: uuid.UUID = field(default_factory=uuid.uuid4)


# TODO: Реализовать Order (dataclass)
# Поля: user_id, id, status, total_amount, created_at, items, status_history
# Методы:
#   - add_item(product_name, price, quantity) -> OrderItem
#   - pay() -> None  [КРИТИЧНО: нельзя оплатить дважды!]
#   - cancel() -> None
#   - ship() -> None
#   - complete() -> None
@dataclass
class Order:
    user_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: OrderStatus=OrderStatus.CREATED
    total_amount: Decimal = field(default=Decimal(0))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    items: List[OrderItem] = field(default_factory=list)
    status_history: List[OrderStatusChange] = field(default_factory=list)



    def __post_init__(self):
        # Добавляем начальный статус в историю, если его нет
        if not self.status_history:
            self.status_history.append(
                OrderStatusChange(
                    order_id=self.id,
                    status=self.status,
                    changed_at=self.created_at
                )
            )
        self._recalculate_total()

    @property
    def total_amount(self) -> Decimal:
        return self._total_amount

    @total_amount.setter
    def total_amount(self, value: Decimal):
        self._total_amount = value

    def _recalculate_total(self):
        """Пересчитать общую сумму заказа."""
        self._total_amount = sum((item.subtotal for item in self.items), Decimal(0))

    def add_item(self, product_name:str, price: Decimal, quantity: int) -> OrderItem: 

        if self.status == OrderStatus.CANCELLED:
            raise OrderCancelledError(self.id)
        
        item = OrderItem(
            product_name=product_name,
            price=price,
            quantity=quantity,
            order_id=self.id,
            )
        self.items.append(item)
        self._recalculate_total()
        #self.total_amount += item.subtotal
        return item 
    
    def pay(self) -> None:
        if self.status == OrderStatus.PAID:
            raise OrderAlreadyPaidError(self.id)
        if self.status == OrderStatus.CANCELLED:
            raise OrderCancelledError(self.id)
        
        self.status = OrderStatus.PAID

    
    def cancel(self) -> None:
        #нельзя отменить оплаченный
        if self.status == OrderStatus.PAID:
            raise OrderAlreadyPaidError(self.id)
        if self.status == OrderStatus.CANCELLED:
            raise OrderCancelledError(self.id)
        self.status = OrderStatus.CANCELLED
    
    def ship(self) -> None:
        if self.status == OrderStatus.CANCELLED:
            raise OrderCancelledError(self.id)
        if self.status != OrderStatus.PAID:
            raise ValueError("Order must be paid before shipping")
        if self.total_amount == 0:  
            raise InvalidAmountError(self.id)
        self.status = OrderStatus.SHIPPED
        
    def complete(self) -> None:
        if self.status != OrderStatus.SHIPPED:
            raise ValueError("Order must be shipped before completion")
        if self.status == OrderStatus.CANCELLED:
            raise OrderCancelledError(self.id)
        self.status = OrderStatus.COMPLETED

