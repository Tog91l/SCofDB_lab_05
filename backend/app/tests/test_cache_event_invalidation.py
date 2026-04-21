"""
LAB 05: Проверка починки через событийную инвалидацию.
"""

import pytest
import uuid
import httpx

from sqlalchemy import text
from app.infrastructure.db import SessionLocal
from app.infrastructure.redis_client import get_redis


@pytest.mark.asyncio
async def test_order_card_is_fresh_after_event_invalidation():
    """
    Сценарий:

    1) Прогреть кэш карточки заказа.
    2) Изменить заказ через mutate-with-event-invalidation.
    3) Проверить что ключ кэша инвалидирован.
    4) Повторный GET возвращает свежие данные.
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

        redis = get_redis()
        cache_key = f"order_card:v1:{order_id}"
        cached_value = await redis.get(cache_key)

        assert cached_value is not None

    
        await client.post(
            f"/api/cache-demo/orders/{order_id}/mutate-with-event-invalidation",
            json={"new_total_amount": 999.0}
        )


        cached_value_after = await redis.get(cache_key)

        assert cached_value_after is None

        second_response = await client.get(
            f"/api/cache-demo/orders/{order_id}/card",
            params={"use_cache": "true"}
        )

        second_data = second_response.json()
        assert second_data["total_amount"] == 999.0
        print("Первое значение total_amount:", first_data["total_amount"])
        print("Новое значение total_amount:", second_data["total_amount"])
        print("Причина: кэш был инвалидирован событием")

        #raise NotImplementedError("TODO: implement event invalidation freshness test")
