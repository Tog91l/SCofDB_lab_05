"""Cache service template for LAB 05."""

from typing import Any
import json
from sqlalchemy import text
from app.infrastructure.redis_client import redis_client
from app.infrastructure.db import SessionLocal

class CacheService:
    """
    Сервис кэширования каталога и карточки заказа.

    TODO:
    - реализовать методы через Redis client + БД;
    - добавить TTL и версионирование ключей.
    """
    def __init__(self, redis_client: Any, repository: Any):
        self.redis = redis_client
        self.repository = repository
        self.ttl = 60

    async def get_catalog(self, *, use_cache: bool = True) -> list[dict[str, Any]]:
        """
        TODO:
        1) Попытаться вернуть catalog из Redis.
        2) При miss загрузить из БД.
        3) Положить в Redis с TTL.
        """
        cache_catalog_key = "catalog:v1"
        if use_cache:
            cached = await self.redis.get(cache_catalog_key)
            if cached:
                return json.loads(cached)
            
        catalog_data = await self.repository.get_catalog() 
        
        await self.redis.set(cache_catalog_key,json.dumps(catalog_data),ex=self.ttl)
        return catalog_data
        #raise NotImplementedError("TODO: implement get_catalog")

    async def get_order_card(self, order_id: str, *, use_cache: bool = True) -> dict[str, Any]:
        """
        TODO:
        1) Попытаться вернуть карточку заказа из Redis.
        2) При miss загрузить из БД.
        3) Положить в Redis с TTL.
        """
        cache_order_key = f"order_card:v1:{order_id}"
        if use_cache:
            cached = await self.redis.get(cache_order_key)
            if cached:
                return json.loads(cached)
        
        card_order = await self.repository.get_order_card(order_id)
        await self.redis.set(cache_order_key, json.dumps(card_order), ex=self.ttl)

        return card_order

        #return card_order

       # raise NotImplementedError("TODO: implement get_order_card")

    async def invalidate_order_card(self, order_id: str) -> None:
        """TODO: Удалить ключ карточки заказа из Redis."""
        cache_order_key = f"order_card:v1:{order_id}"
        await self.redis.delete(cache_order_key)
        #raise NotImplementedError("TODO: implement invalidate_order_card")

    async def invalidate_catalog(self) -> None:
        """TODO: Удалить ключ каталога из Redis."""
        await self.redis.delete("catalog:v1")
