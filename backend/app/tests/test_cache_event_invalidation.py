"""
LAB 05: Проверка починки через событийную инвалидацию.
"""

import pytest


@pytest.mark.asyncio
async def test_order_card_is_fresh_after_event_invalidation():
    """
    TODO: Реализовать сценарий:
    1) Прогреть кэш карточки заказа.
    2) Изменить заказ через mutate-with-event-invalidation.
    3) Убедиться, что ключ карточки инвалидирован.
    4) Повторный GET возвращает свежие данные из БД, а не stale cache.
    """
    raise NotImplementedError("TODO: implement event invalidation freshness test")
