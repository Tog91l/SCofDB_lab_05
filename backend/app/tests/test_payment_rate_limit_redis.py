"""
LAB 05: Rate limiting endpoint оплаты через Redis.
"""

import pytest
import uuid
import httpx
from sqlalchemy import text
from app.infrastructure.redis_client import get_redis
from app.infrastructure.db import SessionLocal

@pytest.mark.asyncio
async def test_payment_endpoint_rate_limit():
    """
    Сценарий:

    1) Создаем заказ.
    2) Отправляем несколько запросов оплаты подряд.
    3) Проверяем что первые запросы проходят.
    4) Проверяем что превышение лимита возвращает 429.
    5) Проверяем заголовки rate limit.
    """
    #order_id = str(uuid.uuid4())
    #user_id = str(uuid.uuid4())

    async with httpx.AsyncClient(base_url="http://localhost:8080") as client:

        order_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        redis = get_redis()
        await redis.delete(f"rate_limit:pay:{user_id}")

       
        limit  = 5
       
        for i in range(limit):
            response = await client.post(
                f"/api/orders/{order_id}/pay",
                headers={"X-User-Id": user_id}
            )

            assert response.status_code != 429
            assert response.headers["X-RateLimit-Limit"] == str(limit)
            assert response.headers["X-RateLimit-Remaining"] == str(limit - (i + 1))

    
        response_429 = await client.post(
            f"/api/orders/{order_id}/pay",
            headers={"X-User-Id": user_id}
        )

        assert response_429.status_code == 429
        assert response_429.json() == {"detail": "Too Many Requests"}

        print("Причина: превышен Redis rate limit")

    #raise NotImplementedError("TODO: implement redis rate limiting test")
