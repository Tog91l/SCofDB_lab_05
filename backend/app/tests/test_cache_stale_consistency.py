"""
LAB 05: Демонстрация неконсистентности кэша.
"""

import pytest
import uuid
import httpx

from sqlalchemy import text
from app.infrastructure.db import SessionLocal

@pytest.mark.asyncio
async def test_stale_order_card_when_db_updated_without_invalidation():
    """
    TODO: Реализовать сценарий:
    1) Прогреть кэш карточки заказа (GET /api/cache-demo/orders/{id}/card?use_cache=true).
    2) Изменить заказ в БД через endpoint mutate-without-invalidation.
    3) Повторно запросить карточку с use_cache=true.
    4) Проверить, что клиент получает stale данные из кэша.
    """
    async with httpx.AsyncClient(base_url="http://localhost:8080") as client:

        order_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())


        async with SessionLocal() as session:
            async with session.begin():

                await session.execute(
                    text("""
                    INSERT INTO users (id, email, name, created_at)
                    VALUES (:user, :email, 'Test', NOW())
                    """),
                    {"user": user_id, "email": f"{user_id}@mail.com"}
                )

                await session.execute(
                    text("""
                    INSERT INTO orders (id, user_id, status, total_amount, created_at)
                    VALUES (:order, :user, 'created', 100.0, NOW())
                    """),
                    {"order": order_id, "user": user_id}
                )

        first_response = await client.get(
            f"/api/cache-demo/orders/{order_id}/card",
            params={"use_cache": "true"}
        )

        first_data = first_response.json()

        await client.post(
            f"/api/cache-demo/orders/{order_id}/mutate-without-invalidation",
            json={"new_total_amount": 999.0}
        )

        second_response = await client.get(
            f"/api/cache-demo/orders/{order_id}/card",
            params={"use_cache": "true"}
        )

        second_data = second_response.json()

        assert second_data["total_amount"] == first_data["total_amount"]
        print("Первое значение total_amount:", first_data["total_amount"])
        print("Второе значение total_amount:", second_data["total_amount"])
        print("Причина: кэш не был инвалидирован после изменения БД")
