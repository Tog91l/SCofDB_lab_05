"""Cache service template for LAB 05."""

from typing import Any


class CacheService:
    """
    Сервис кэширования каталога и карточки заказа.

    TODO:
    - реализовать методы через Redis client + БД;
    - добавить TTL и версионирование ключей.
    """

    async def get_catalog(self, *, use_cache: bool = True) -> list[dict[str, Any]]:
        """
        TODO:
        1) Попытаться вернуть catalog из Redis.
        2) При miss загрузить из БД.
        3) Положить в Redis с TTL.
        """
        raise NotImplementedError("TODO: implement get_catalog")

    async def get_order_card(self, order_id: str, *, use_cache: bool = True) -> dict[str, Any]:
        """
        TODO:
        1) Попытаться вернуть карточку заказа из Redis.
        2) При miss загрузить из БД.
        3) Положить в Redis с TTL.
        """
        raise NotImplementedError("TODO: implement get_order_card")

    async def invalidate_order_card(self, order_id: str) -> None:
        """TODO: Удалить ключ карточки заказа из Redis."""
        raise NotImplementedError("TODO: implement invalidate_order_card")

    async def invalidate_catalog(self) -> None:
        """TODO: Удалить ключ каталога из Redis."""
        raise NotImplementedError("TODO: implement invalidate_catalog")
