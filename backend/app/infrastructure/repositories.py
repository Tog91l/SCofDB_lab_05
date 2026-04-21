
"""Реализация репозиториев с использованием SQLAlchemy."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user import User
from app.domain.order import Order, OrderItem, OrderStatus, OrderStatusChange


class UserRepository:
    """Репозиторий для User."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # TODO: Реализовать save(user: User) -> None
    # Используйте INSERT ... ON CONFLICT DO UPDATE
    async def save(self, user: User) -> None:

        save_sql_user = text ( '''  INSERT INTO users(id, email, name, created_at) VALUES (:id, :email, :name, :created_at)
                              ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name '''

        )
        await self.session.execute(
            save_sql_user, {
                 "id": user.id,
                 "email": user.email,
                 "name": user.name,
                 "created_at": user.created_at,
            },
        )
        await self.session.commit()
        #raise NotImplementedError("TODO: Реализовать UserRepository.save")

    # TODO: Реализовать find_by_id(user_id: UUID) -> Optional[User]
    async def find_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        find_id = text (''' SELECT * FROM users WHERE id = :user_id''')
        
        result = await self.session.execute ( find_id, {'user_id': user_id})
        row = result.fetchone()
        if not row:
            return None 
        return User (
            id=row.id,
            email=row.email,
            name=row.name,
            created_at=row.created_at,
        )
        #raise NotImplementedError("TODO: Реализовать UserRepository.find_by_id")

    # TODO: Реализовать find_by_email(email: str) -> Optional[User]
    async def find_by_email(self, email: str) -> Optional[User]:
        find_em = text (''' SELECT * FROM users WHERE email =:email''')
        result = await self.session.execute ( find_em, {'email': email})
        row = result.fetchone()
        if not row:
            return None 
        return User (
            id=row.id,
            email=row.email,
            name=row.name,
            created_at=row.created_at,
        )
        #raise NotImplementedError("TODO: Реализовать UserRepository.find_by_email")

    # TODO: Реализовать find_all() -> List[User]
    async def find_all(self) -> List[User]:
        all_users = text (''' SELECT * FROM users ORDER BY created_at DESC''')
        result = await self.session.execute (all_users)
        users = []
        for row in result.fetchall():
            users.append(User(
            id=row.id,
            email=row.email,
            name=row.name,
            created_at=row.created_at,
        ))
        return users

        #raise NotImplementedError("TODO: Реализовать UserRepository.find_all")


class OrderRepository:
    """Репозиторий для Order."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # TODO: Реализовать save(order: Order) -> None
    # Сохранить заказ, товары и историю статусов
    async def save(self, order: Order) -> None:
        save_order= text("""
            INSERT INTO orders (id, user_id, status, total_amount, created_at)
            VALUES (:id, :user_id, :status, :total_amount, :created_at)
            ON CONFLICT (id)
            DO UPDATE SET
                status = EXCLUDED.status,
                total_amount = EXCLUDED.total_amount
        """)
        await self.session.execute(
            save_order, {
            "id": order.id,
            "user_id": order.user_id,
            "status": order.status.value,
            "total_amount": float(order.total_amount),
            "created_at": order.created_at,
        })
        await self.session.execute(text("DELETE FROM order_items WHERE order_id = :order_id"),{"order_id": order.id},)

        for item in order.items:
            await self.session.execute(
                text("""INSERT INTO order_items (id, order_id, product_name, price, quantity)
                    VALUES (:id, :order_id, :product_name, :price, :quantity)
                """),
                {
                    "id": item.id,
                    "order_id": order.id,
                    "product_name": item.product_name,
                    "price": float(item.price),
                    "quantity": item.quantity,
                },
            )
        for status_change in order.status_history:
            save_history = text("""
                INSERT INTO order_status_history (id, order_id, status, changed_at)
                VALUES (:id, :order_id, :status, :changed_at)
                ON CONFLICT (id) DO NOTHING
            """)
            
            await self.session.execute(
                save_history,
                {
                    "id": status_change.id,
                    "order_id": order.id,
                    "status": status_change.status.value,
                    "changed_at": status_change.changed_at,
                }
            )
        
        await self.session.commit()
        #raise NotImplementedError("TODO: Реализовать OrderRepository.save")

    # TODO: Реализовать find_by_id(order_id: UUID) -> Optional[Order]
    # Загрузить заказ со всеми товарами и историей
    # Используйте object.__new__(Order) чтобы избежать __post_init__
    async def find_by_id(self, order_id: uuid.UUID) -> Optional[Order]:
        result = await self.session.execute(
            text("SELECT * FROM orders WHERE id = :id"),
            {"id": order_id},
        )

        row = result.fetchone()
        if not row:
            return None
        
        order = object.__new__(Order)
        order.id = row.id
        order.user_id = row.user_id
        order.status = OrderStatus(row.status)
        order.total_amount = Decimal(str(row.total_amount)) if row.total_amount else Decimal(0)
        order.created_at = row.created_at
        order.items = []
        order.status_history = []

        result = await self.session.execute( text("SELECT * FROM order_items WHERE order_id = :order_id"),
            {"order_id": order_id},
        )

        for item_row in result.fetchall():
            item = object.__new__(OrderItem)
            item.id = item_row.id 
            item.order_id = item_row.order_id
            item.product_name = item_row.product_name
            item.price = Decimal(str(item_row.price))
            item.quantity = item_row.quantity
            order.items.append(item)

        result = await self.session.execute(
            text("""SELECT * FROM order_status_history WHERE order_id = :order_id
                ORDER BY changed_at """),
            {"order_id": order_id},
        )
        for history_row in result.fetchall():
            history = object.__new__(OrderStatusChange)
            history.id = history_row.id
            history.order_id = history_row.order_id
            history.status = OrderStatus(history_row.status)
            history.changed_at = history_row.changed_at
            order.status_history.append(history)

        return order


        #raise NotImplementedError("TODO: Реализовать OrderRepository.find_by_id")

    # TODO: Реализовать find_by_user(user_id: UUID) -> List[Order]
    async def find_by_user(self, user_id: uuid.UUID) -> List[Order]:
        result = await self.session.execute(
            text("SELECT id FROM orders WHERE user_id = :user_id"),
            {"user_id": user_id},
        )

        orders = []
        for row in result.fetchall():
            order = await self.find_by_id(row.id)
            if order:
                orders.append(order)

        return orders
        #raise NotImplementedError("TODO: Реализовать OrderRepository.find_by_user")

    # TODO: Реализовать find_all() -> List[Order]
    async def find_all(self) -> List[Order]:
        result = await self.session.execute(
            text("SELECT id FROM orders ORDER BY created_at DESC")
        )

        orders = []
        for row in result.fetchall():
            order = await self.find_by_id(row.id)
            if order:
                orders.append(order)
        return orders
        #raise NotImplementedError("TODO: Реализовать OrderRepository.find_all")
