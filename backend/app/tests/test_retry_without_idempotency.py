"""
LAB 04: Демонстрация проблемы retry без идемпотентности.

Сценарий:
1) Клиент отправил запрос на оплату.
2) До получения ответа \"сеть оборвалась\" (моделируем повтором запроса).
3) Клиент повторил запрос БЕЗ Idempotency-Key.
4) В unsafe-режиме возможна двойная оплата.
"""

import pytest
import asyncio
import httpx
import uuid
from sqlalchemy import text
from app.infrastructure.db import SessionLocal



@pytest.mark.asyncio
async def test_retry_without_idempotency_can_double_pay():
    async with httpx.AsyncClient(base_url="http://backend:8080") as client:
        order_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        async with SessionLocal() as session:
            async with session.begin():
                await session.execute(
                text("INSERT INTO users (id, email, name, created_at) VALUES (:user, :email, 'Test', NOW())"), 
                {"user": user_id, "email": f"{user_id}@gmail.com"}
            )
                await session.execute(
                text("INSERT INTO orders (id, user_id, status, total_amount, created_at) " \
                "VALUES (:order, :user, 'created', 300.0, NOW())"),
                {"order": order_id, "user": user_id}
            )
                
        payload = {"order_id": order_id, "mode": "unsafe"}
        
        await asyncio.gather(
            client.post("/api/payments/retry-demo", json=payload),
            client.post("/api/payments/retry-demo", json=payload)
        )
        
        async with SessionLocal() as session:
            result = await session.execute(
                text("SELECT status FROM order_status_history WHERE order_id = :order AND status = 'paid'"), 
                {"order": order_id}
            )
        
        all_paid_count = len(result.fetchall())
    assert all_paid_count > 1
    print("")
    print(f"Количество попыток оплаты заказа: {all_paid_count}")
    print("Причина: после сбоя в сети клиент попробовал оплататить ззаказ еще раз. Без Idempotency-Key сервер обработал запросы как разные, независимо" \
    "Поэтому оплата прошла два раза")

    """
    TODO: Реализовать тест.

    Рекомендуемые шаги:
    1) Создать заказ в статусе created.
    2) Выполнить две параллельные попытки POST /api/payments/retry-demo
       с mode='unsafe' и БЕЗ заголовка Idempotency-Key.
    3) Проверить историю order_status_history:
       - paid-событий больше 1 (или иная метрика двойного списания).
    4) Вывести понятный отчёт в stdout:
       - сколько попыток
       - сколько paid в истории
       - почему это проблема.
    """
    #raise NotImplementedError("TODO: Реализовать retry-сценарий без идемпотентности")

