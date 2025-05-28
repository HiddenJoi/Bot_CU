import pytest
import os
from config import Config

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Настройка тестового окружения"""
    # Устанавливаем тестовые значения для конфигурации
    os.environ["SIMILARITY_THRESHOLD"] = "0.7"
    os.environ["CONTEXT_FILE"] = "test_context.txt"
    
    # Создаем тестовый контекстный файл
    with open("test_context.txt", "w", encoding="utf-8") as f:
        f.write("""Как открыть вклад в банке? Для открытия вклада нужно прийти в отделение с паспортом.

Как пополнить карту? Пополнение возможно через банкомат или мобильное приложение.

Как получить кредит? Для получения кредита нужна справка о доходах и паспорт.""")

    yield

    # Очистка после тестов
    if os.path.exists("test_context.txt"):
        os.remove("test_context.txt") 