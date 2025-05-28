import pytest
import json
import os
import asyncio
from datetime import datetime
from contexts import DialogContext, ContextManager
from config import config

@pytest.fixture
def context_manager():
    """Фикстура для создания экземпляра ContextManager"""
    return ContextManager()

@pytest.fixture
def test_user_id():
    """Фикстура с тестовым ID пользователя"""
    return 12345

@pytest.fixture
def test_context_file(test_user_id):
    """Фикстура с путем к тестовому файлу контекста"""
    return f"contexts/{test_user_id}.json"

@pytest.fixture(autouse=True)
def cleanup():
    """Фикстура для очистки тестовых файлов после каждого теста"""
    yield
    # Очищаем все тестовые файлы контекста
    for file in os.listdir("contexts"):
        if file.endswith(".json"):
            os.remove(os.path.join("contexts", file))

def test_create_context(context_manager, test_user_id):
    """Тест создания нового контекста"""
    context = context_manager.get_context(test_user_id)
    assert isinstance(context, DialogContext)
    assert context.user_id == test_user_id
    assert context.slots == {}
    assert context.message_history == []

def test_get_existing_context(context_manager, test_user_id):
    """Тест получения существующего контекста"""
    context1 = context_manager.get_context(test_user_id)
    context2 = context_manager.get_context(test_user_id)
    assert context1 is context2  # Проверяем, что возвращается тот же объект

def test_update_slot(context_manager, test_user_id, test_context_file):
    """Тест обновления слота контекста"""
    context = context_manager.get_context(test_user_id)
    context.update_slot("user_name", "Иван")
    assert context.get_slot("user_name") == "Иван"
    
    # Проверяем сохранение в файл
    assert os.path.exists(test_context_file)
    with open(test_context_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert data['slots']['user_name'] == "Иван"

def test_add_message(context_manager, test_user_id, test_context_file):
    """Тест добавления сообщения в историю"""
    context = context_manager.get_context(test_user_id)
    context.add_message("Тестовое сообщение", True)
    messages = context.get_last_messages()
    assert len(messages) == 1
    assert messages[0]['text'] == "Тестовое сообщение"
    assert messages[0]['is_user'] is True

def test_message_history_limit(context_manager, test_user_id):
    """Тест ограничения истории сообщений"""
    context = context_manager.get_context(test_user_id)
    # Добавляем 6 сообщений
    for i in range(6):
        context.add_message(f"Сообщение {i}", True)
    messages = context.get_last_messages()
    assert len(messages) == 5  # Проверяем, что сохранились только последние 5

def test_clear_context(context_manager, test_user_id, test_context_file):
    """Тест очистки контекста"""
    context = context_manager.get_context(test_user_id)
    context.update_slot("user_name", "Иван")
    context.add_message("Тестовое сообщение", True)
    
    context.clear_context()
    assert context.slots == {}
    assert context.message_history == []
    
    # Проверяем, что файл контекста тоже очищен
    with open(test_context_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert data['slots'] == {}
        assert data['message_history'] == []

def test_context_manager_cleanup(context_manager, test_user_id, test_context_file):
    """Тест очистки контекста через менеджер"""
    context = context_manager.get_context(test_user_id)
    context.update_slot("user_name", "Иван")
    
    context_manager.clear_context(test_user_id)
    assert test_user_id not in context_manager.contexts
    assert not os.path.exists(test_context_file)

def test_corrupted_context_file(context_manager, test_user_id, test_context_file):
    """Тест обработки поврежденного файла контекста"""
    # Создаем поврежденный JSON файл
    with open(test_context_file, 'w', encoding='utf-8') as f:
        f.write("{invalid json")
    
    # Должен создаться новый контекст
    context = context_manager.get_context(test_user_id)
    assert context.slots == {}
    assert context.message_history == []

def test_large_context_file(context_manager, test_user_id, test_context_file):
    """Тест работы с большим файлом контекста"""
    context = context_manager.get_context(test_user_id)
    # Добавляем много сообщений
    for i in range(100):
        context.add_message(f"Сообщение {i}" * 100, True)
    
    # Проверяем, что файл создан и не превышает разумный размер
    assert os.path.exists(test_context_file)
    assert os.path.getsize(test_context_file) < 1024 * 1024  # Меньше 1MB

@pytest.mark.asyncio
async def test_concurrent_access(context_manager, test_user_id):
    """Тест конкурентного доступа к контексту"""
    async def update_context():
        context = context_manager.get_context(test_user_id)
        context.update_slot("counter", str(int(context.get_slot("counter") or 0) + 1))
    
    # Создаем начальный контекст
    context = context_manager.get_context(test_user_id)
    context.update_slot("counter", "0")
    
    # Запускаем несколько асинхронных обновлений
    tasks = [update_context() for _ in range(10)]
    await asyncio.gather(*tasks)
    
    # Проверяем результат
    final_context = context_manager.get_context(test_user_id)
    assert int(final_context.get_slot("counter")) == 10 