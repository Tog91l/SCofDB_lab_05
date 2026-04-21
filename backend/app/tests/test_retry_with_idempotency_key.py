"""
LAB 04: Проверка идемпотентного повтора запроса.

Цель:
При повторном запросе с тем же Idempotency-Key вернуть
кэшированный результат без повторного списания.
"""

import pytest
import asyncio
import httpx
import uuid
from sqlalchemy import text
from app.infrastructure.db import SessionLocal


@pytest.mark.asyncio
async def test_retry_with_same_key_returns_cached_response():
    """
    TODO: Реализовать тест.

    Рекомендуемые шаги:
    1) Создать заказ в статусе created.
    2) Сделать первый POST /api/payments/retry-demo (mode='unsafe')
       с заголовком Idempotency-Key: fixed-key-123.
    3) Повторить тот же POST с тем же ключом и тем же payload.
    4) Проверить:
       - второй ответ пришёл из кэша (через признак, который вы добавите,
         например header X-Idempotency-Replayed=true),
       - в order_status_history только одно событие paid,
       - в idempotency_keys есть запись completed с response_body/status_code.
    """
    async with httpx.AsyncClient(base_url="http://backend:8080") as client:

        order_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        key = "fixed-key-123"
        async with SessionLocal() as session:
            async with session.begin():

                await session.execute(
                    text(
                        "INSERT INTO users (id, email, name, created_at) "
                        "VALUES (:user, :email, 'Test', NOW())"
                    ),
                    {"user": user_id, "email": f"{user_id}@gmail.com"}
                )

                await session.execute(
                    text(
                        "INSERT INTO orders (id, user_id, status, total_amount, created_at) "
                        "VALUES (:order, :user, 'created', 300.0, NOW())"
                    ),
                    {"order": order_id, "user": user_id}
                )
        payload = {"order_id": order_id,"mode": "unsafe"}
        headers = {"Idempotency-Key": key}

        respon1 = await client.post("/api/payments/retry-demo",json=payload,headers=headers)
        assert respon1.status_code == 200

        respon2 = await client.post( "/api/payments/retry-demo", json=payload, headers=headers)
        assert respon2.status_code == 200
        assert respon2.headers.get("X-Idempotency-Replayed") == "true"

        async with SessionLocal() as session:
            result = await session.execute(
                text(
                    "SELECT status FROM order_status_history "
                    "WHERE order_id = :order AND status = 'paid'"
                ),{"order": order_id}
            )

            all_paid_count = len(result.fetchall())
            assert all_paid_count == 1 
            async with SessionLocal() as session:
                result = await session.execute(
                text("SELECT status FROM idempotency_keys WHERE idempotency_key = :key"),
                {"key": key}
            )
            row = result.fetchone()
            assert row[0] == "completed"

            print("Первый запрос:", respon1.status_code)
            print("Второй запрос:", respon2.status_code)
            print("Сколько раз прошла оплата:", all_paid_count)






    #raise NotImplementedError("TODO: Реализовать retry-сценарий с Idempotency-Key")


@pytest.mark.asyncio
async def test_same_key_different_payload_returns_conflict():
    """
    TODO: Реализовать негативный тест.

    Один и тот же Idempotency-Key нельзя использовать с другим payload.
    Ожидается 409 Conflict (или эквивалентная бизнес-ошибка).
    """
    async with httpx.AsyncClient(base_url="http://backend:8080") as client:

      order_id = str(uuid.uuid4())
      user_id = str(uuid.uuid4())
      key = "fixed-key-conflict"

        # создаем пользователя и заказ
      async with SessionLocal() as session:
            async with session.begin():

                await session.execute(
                    text("INSERT INTO users (id, email, name, created_at) VALUES (:user, :email, 'Test', NOW())"
                    ), {"user": user_id, "email": f"{user_id}@gmail.com"}
                )

                await session.execute(
                    text("INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES (:order, :user, 'created', 300.0, NOW())"
                    ),{"order": order_id, "user": user_id}
                )

      headers = {"Idempotency-Key": key}

      payload1 = {"order_id": order_id,"mode": "unsafe"}
      payload2 = { "order_id": order_id,"mode": "safe"}

      
      respon1 = await client.post("/api/payments/retry-demo",json=payload1,headers=headers)
      respon2 = await client.post("/api/payments/retry-demo",json=payload2,headers=headers)

      print("Первый запрос:", respon1.status_code)
      print("Второй запрос (другой payload):", respon2.status_code)
    #raise NotImplementedError("TODO: Реализовать проверку конфликта payload для одного key")
