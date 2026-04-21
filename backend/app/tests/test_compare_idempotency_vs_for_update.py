"""
LAB 04: Сравнение подходов
1) FOR UPDATE (решение из lab_02)
2) Idempotency-Key + middleware (lab_04)
"""

import pytest
import httpx
import uuid
from sqlalchemy import text
from app.infrastructure.db import SessionLocal

@pytest.mark.asyncio
async def test_compare_for_update_and_idempotency_behaviour():
    """
    TODO: Реализовать сравнительный тест/сценарий.

    Минимум сравнения:
    1) Повтор запроса с mode='for_update':
       - защита от гонки на уровне БД,
       - повтор может вернуть бизнес-ошибку \"already paid\".
    2) Повтор запроса с mode='unsafe' + Idempotency-Key:
       - второй вызов возвращает тот же кэшированный успешный ответ,
         без повторного списания.

    В конце добавьте вывод:
    - чем отличаются цели и UX двух подходов,
    - почему они не взаимоисключающие и могут использоваться вместе.
    """
    async with httpx.AsyncClient(base_url="http://backend:8080") as client:

        #тест for update 
        order_id_1 = str(uuid.uuid4())
        user_id_1 = str(uuid.uuid4())

        async with SessionLocal() as session:
            async with session.begin():

                await session.execute(
                    text("INSERT INTO users (id, email, name, created_at) VALUES (:user, :email, 'Test', NOW())"
                    ),{"user": user_id_1, "email": f"{user_id_1}@gmail.com"}
                )

                await session.execute(
                    text("INSERT INTO orders (id, user_id, status, total_amount, created_at) " \
                    "VALUES (:order, :user, 'created', 300.0, NOW())"
                    ),
                    {"order": order_id_1, "user": user_id_1}
                )

        payload_for_update = {"order_id": order_id_1,"mode": "for_update"}

        respon1 = await client.post("/api/payments/retry-demo", json=payload_for_update)
        respon2 = await client.post("/api/payments/retry-demo", json=payload_for_update)

        async with SessionLocal() as session:
            result = await session.execute(
                text( "SELECT status FROM order_status_history WHERE order_id = :order AND status='paid'"
                ),{"order": order_id_1}
            )

            all_paid_for_update = len(result.fetchall())

        order_id_2 = str(uuid.uuid4())
        user_id_2 = str(uuid.uuid4())
        key = "compare-key-123"

        async with SessionLocal() as session:
            async with session.begin():

                await session.execute(
                    text("INSERT INTO users (id, email, name, created_at) VALUES (:user, :email, 'Test', NOW())"
                    ),{"user": user_id_2, "email": f"{user_id_2}@gmail.com"}
                )

                await session.execute(
                    text("INSERT INTO orders (id, user_id, status, total_amount, created_at) "
                        "VALUES (:order, :user, 'created', 300.0, NOW())"
                    ),{"order": order_id_2, "user": user_id_2}
                )

        payload_idempotent = {"order_id": order_id_2,"mode": "unsafe"}

        headers = {"Idempotency-Key": key}

        respon3 = await client.post("/api/payments/retry-demo",json=payload_idempotent,headers=headers)
        respon4 = await client.post("/api/payments/retry-demo",json=payload_idempotent,headers=headers)

        async with SessionLocal() as session:
            result = await session.execute(
                text("SELECT status FROM order_status_history WHERE order_id = :order AND status='paid'"
                ),{"order": order_id_2}
            )

            all_paid_idempotent = len(result.fetchall())
    print("Сравнение FOR UPDATE vs Idempotency-Key")
    print("FOR UPDATE:")
    print("Первый запрос:", respon1.status_code)
    print("Второй запрос:", respon2.status_code)
    print("Количество оплаты заказа:", all_paid_for_update)

    print()
    print("Idempotency-Key:")
    print("Первый запрос:", respon3.status_code)
    print("Второй запрос:", respon4.status_code)
    print("Количество оплаты заказа:", all_paid_idempotent)
