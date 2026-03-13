"""Event-driven cache invalidation template for LAB 05."""

from dataclasses import dataclass


@dataclass
class OrderUpdatedEvent:
    """Событие изменения заказа."""

    order_id: str


class CacheInvalidationEventBus:
    """
    Минимальный event bus для LAB 05.

    TODO:
    - реализовать publish/subscribe;
    - на OrderUpdatedEvent инвалидировать:
      - order_card:v1:{order_id}
      - catalog:v1 (если изменение затрагивает агрегаты каталога).
    """

    async def publish_order_updated(self, event: OrderUpdatedEvent) -> None:
        raise NotImplementedError("TODO: implement publish_order_updated")
