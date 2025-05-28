import pytest
from unittest.mock import AsyncMock, patch
from services.openai_service import OpenAIService
from config import config

@pytest.fixture
def openai_service():
    """Фикстура для создания экземпляра OpenAIService"""
    return OpenAIService()

@pytest.fixture
def mock_chat_history():
    """Фикстура с тестовой историей чата"""
    return [
        {"message": "Как открыть вклад?", "is_from_user": True},
        {"message": "Для открытия вклада нужно прийти в отделение с паспортом.", "is_from_user": False},
        {"message": "А какие документы нужны?", "is_from_user": True}
    ]

@pytest.mark.asyncio
async def test_get_chat_completion_success(openai_service):
    """Тест успешного получения ответа от OpenAI"""
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "Тестовый ответ"
    
    with patch('openai.AsyncOpenAI.chat.completions.create', return_value=mock_response):
        response = await openai_service.get_chat_completion([{"role": "user", "content": "Тест"}])
        assert response == "Тестовый ответ"

@pytest.mark.asyncio
async def test_get_chat_completion_error(openai_service):
    """Тест обработки ошибки при получении ответа от OpenAI"""
    with patch('openai.AsyncOpenAI.chat.completions.create', side_effect=Exception("API Error")):
        response = await openai_service.get_chat_completion([{"role": "user", "content": "Тест"}])
        assert response == "Извините, произошла ошибка при обработке запроса."

def test_format_messages(openai_service, mock_chat_history):
    """Тест форматирования сообщений для OpenAI API"""
    formatted = openai_service.format_messages(mock_chat_history)
    assert len(formatted) == 3
    assert formatted[0]["role"] == "user"
    assert formatted[1]["role"] == "assistant"
    assert formatted[2]["role"] == "user"
    assert formatted[0]["content"] == "Как открыть вклад?"

def test_format_messages_empty(openai_service):
    """Тест форматирования пустого списка сообщений"""
    formatted = openai_service.format_messages([])
    assert len(formatted) == 0

def test_format_messages_invalid_role(openai_service):
    """Тест форматирования сообщений с некорректной ролью"""
    invalid_history = [
        {"message": "Тест", "is_from_user": True},
        {"message": "Ответ", "is_from_user": None}  # Некорректная роль
    ]
    formatted = openai_service.format_messages(invalid_history)
    assert len(formatted) == 1  # Только валидное сообщение должно быть включено
    assert formatted[0]["role"] == "user"

def test_format_messages_long_content(openai_service):
    """Тест форматирования сообщений с длинным содержимым"""
    long_message = "Тест" * 1000  # Создаем длинное сообщение
    history = [{"message": long_message, "is_from_user": True}]
    formatted = openai_service.format_messages(history)
    assert len(formatted) == 1
    assert formatted[0]["content"] == long_message

def test_max_tokens_setting(openai_service):
    """Тест установки максимального количества токенов"""
    assert openai_service.max_tokens == config.MAX_TOKENS

@pytest.mark.asyncio
async def test_get_chat_completion_empty_messages(openai_service):
    """Тест получения ответа с пустым списком сообщений"""
    with pytest.raises(ValueError):
        await openai_service.get_chat_completion([])

@pytest.mark.asyncio
async def test_get_chat_completion_invalid_messages(openai_service):
    """Тест получения ответа с некорректными сообщениями"""
    invalid_messages = [{"invalid_key": "value"}]
    with pytest.raises(ValueError):
        await openai_service.get_chat_completion(invalid_messages) 