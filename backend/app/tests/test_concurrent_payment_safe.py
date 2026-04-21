"""
Тест для демонстрации РЕШЕНИЯ проблемы race condition.

Этот тест должен ПРОХОДИТЬ, подтверждая, что при использовании
pay_order_safe() заказ оплачивается только один раз.
"""

import asyncio
import pytest
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.application.payment_service import PaymentService
from app.domain.exceptions import OrderAlreadyPaidError


# TODO: Настроить подключение к тестовой БД
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/marketplace"


@pytest.fixture
async def db_session():
    """
    Создать сессию БД для тестов.
    
    TODO: Реализовать фикстуру (см. test_concurrent_payment_unsafe.py)
    """
    engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    AsyncSessionLocal = sessionmaker(engine,class_=AsyncSession)
    async with AsyncSessionLocal() as session:
        yield session
    await engine.dispose()

    # TODO: Реализовать создание сессии
    #raise NotImplementedError("TODO: Реализовать db_session fixture")


@pytest.fixture
async def test_order(db_session):
    """
    Создать тестовый заказ со статусом 'created'.
    
    TODO: Реализовать фикстуру (см. test_concurrent_payment_unsafe.py)
    """
    user_id = uuid.uuid4()
    order_id = uuid.uuid4()

    test_user = {"id": user_id, "email": "testuser34@t.com", "name": "Test User"}
    order_test = {"id": order_id, "user_id": user_id, "status": "created", "total_amount": 456}
    session = db_session

    async with session.begin():
        await session.execute(text("""
        INSERT INTO users (id, email, name) 
        VALUES (id, :email, :name, NOW())
    """), test_user)
        await session.execute(text("""
        INSERT INTO orders (id, user_id, status, total_amount)
        VALUES (:id, :user_id, :status, :total_amount, NOW())
    """), order_test)
        await session.execute(text("""
        INSERT INTO order_status_history (id, order_id, status, changed_at)
        VALUES (gen_random_uuid(), :order_id, 'created',NOW())
    """), {"order_id": order_id})

    yield order_id
    
    await session.execute(
            text("DELETE FROM order_status_history WHERE order_id = :order_id"),
            {"order_id": order_id})
    await session.execute(
            text("DELETE FROM orders WHERE id = :order_id"),
            {"order_id": order_id})
    await session.execute(
            text("DELETE FROM users WHERE id = :user_id"),
            {"user_id": user_id})
    
    await session.commit()
    # TODO: Реализовать создание тестового заказа
    #raise NotImplementedError("TODO: Реализовать test_order fixture")

@pytest.mark.asyncio
async def test_concurrent_payment_safe_prevents_race_condition(db_session, test_order):

    order_id = test_order
    session = db_session

    engine_1 = create_async_engine(DATABASE_URL)
    engine_2 = create_async_engine(DATABASE_URL)

    async def payment_attempt_1():
        async with AsyncSession(engine_1) as session1:
            service1 = PaymentService(session1)
            return await service1.pay_order_safe(order_id)

    async def payment_attempt_2():
        async with AsyncSession(engine_2) as session2:
            service2 = PaymentService(session2)
            return await service2.pay_order_safe(order_id)

    results = await asyncio.gather(
        payment_attempt_1(),
        payment_attempt_2(),
        return_exceptions=True
    )
    success_att = sum(1 for r in results if not isinstance(r, Exception))
    error_att = sum(1 for r in results if isinstance(r, Exception))

    assert success_att == 1, f"Ожидалась одна успешная оплата"
    assert error_att == 1, "Ожидалась одна неудачная попытка"

    service = PaymentService(session)
    history = await service.get_payment_history(order_id)
    
    # ОЖИДАЕМ ОДНУ ЗАПИСЬ 'paid' - проблема решена!
    assert len(history) == 1, "Ожидалась 1 запись об оплате (БЕЗ RACE CONDITION!)"
    
    engine_1.dispose()
    engine_2.dispose()
    
    print(f"✅ RACE CONDITION PREVENTED!")
    print(f"Order {order_id} was paid only ONCE:")
    print(f"  - {history[0]['changed_at']}: status = {history[0]['status']}")
    print(f"Second attempt was rejected: {results[1]}")
    


    """
    Тест демонстрирует решение проблемы race condition с помощью pay_order_safe().
    
    ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Тест ПРОХОДИТ, подтверждая, что заказ был оплачен только один раз.
    Это показывает, что метод pay_order_safe() защищен от конкурентных запросов.
    
    TODO: Реализовать тест следующим образом:
    
    1. Создать два экземпляра PaymentService с РАЗНЫМИ сессиями
       (это имитирует два независимых HTTP-запроса)
       
    2. Запустить два параллельных вызова pay_order_safe():
       
       async def payment_attempt_1():
           service1 = PaymentService(session1)
           return await service1.pay_order_safe(order_id)
           
       async def payment_attempt_2():
           service2 = PaymentService(session2)
           return await service2.pay_order_safe(order_id)
           
       results = await asyncio.gather(
           payment_attempt_1(),
           payment_attempt_2(),
           return_exceptions=True
       )
       
    3. Проверить результаты:
       - Одна попытка должна УСПЕШНО завершиться
       - Вторая попытка должна выбросить OrderAlreadyPaidError ИЛИ вернуть ошибку
       
       success_count = sum(1 for r in results if not isinstance(r, Exception))
       error_count = sum(1 for r in results if isinstance(r, Exception))
       
       assert success_count == 1, "Ожидалась одна успешная оплата"
       assert error_count == 1, "Ожидалась одна неудачная попытка"
       
    4. Проверить историю оплат:
       
       service = PaymentService(session)
       history = await service.get_payment_history(order_id)
       
       # ОЖИДАЕМ ОДНУ ЗАПИСЬ 'paid' - проблема решена!
       assert len(history) == 1, "Ожидалась 1 запись об оплате (БЕЗ RACE CONDITION!)"
       
    5. Вывести информацию об успешном решении:
       
       print(f"✅ RACE CONDITION PREVENTED!")
       print(f"Order {order_id} was paid only ONCE:")
       print(f"  - {history[0]['changed_at']}: status = {history[0]['status']}")
       print(f"Second attempt was rejected: {results[1]}")
    """
    # TODO: Реализовать тест, демонстрирующий решение race condition
    #raise NotImplementedError("TODO: Реализовать test_concurrent_payment_safe")


@pytest.mark.asyncio
async def test_concurrent_payment_safe_with_explicit_timing(db_session, test_order):
    """
    Дополнительный тест: проверить работу блокировок с явной задержкой.
    
    TODO: Реализовать тест с добавлением задержки в первой транзакции:
    
    1. Первая транзакция:
       - Начать транзакцию
       - Заблокировать заказ (FOR UPDATE)
       - Добавить задержку (asyncio.sleep(1))
       - Оплатить
       - Commit
       
    2. Вторая транзакция (запустить через 0.1 секунды после первой):
       - Начать транзакцию
       - Попытаться заблокировать заказ (FOR UPDATE)
       - ДОЛЖНА ЖДАТЬ освобождения блокировки от первой транзакции
       - После освобождения - увидеть обновленный статус 'paid'
       - Выбросить OrderAlreadyPaidError
       
    3. Проверить временные метки:
       - Вторая транзакция должна завершиться ПОЗЖЕ первой
       - Разница должна быть >= 1 секунды (время задержки)
       
    Это подтверждает, что FOR UPDATE действительно блокирует строку.
    """
    # TODO: Реализовать тест с проверкой блокировки
    #raise NotImplementedError("TODO: Реализовать test_concurrent_payment_safe_with_explicit_timing")


@pytest.mark.asyncio
async def test_concurrent_payment_safe_multiple_orders():
    
    """
    Дополнительный тест: проверить, что блокировки не мешают разным заказам.
    
    TODO: Реализовать тест:
    1. Создать ДВА разных заказа
    2. Оплатить их ПАРАЛЛЕЛЬНО с помощью pay_order_safe()
    3. Проверить, что ОБА успешно оплачены
    
    Это показывает, что FOR UPDATE блокирует только конкретную строку,
    а не всю таблицу, что важно для производительности.
    """
    # TODO: Реализовать тест с несколькими заказами
    #raise NotImplementedError("TODO: Реализовать test_concurrent_payment_safe_multiple_orders")


if __name__ == "__main__":
    """
    Запуск теста:
    
    cd backend
    export PYTHONPATH=$(pwd)
    pytest app/tests/test_concurrent_payment_safe.py -v -s
    
    ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
    ✅ test_concurrent_payment_safe_prevents_race_condition PASSED
    
    Вывод должен показывать:
    ✅ RACE CONDITION PREVENTED!
    Order XXX was paid only ONCE:
      - 2024-XX-XX: status = paid
    Second attempt was rejected: OrderAlreadyPaidError(...)
    """
    pytest.main([__file__, "-v", "-s"])
