from openai import AsyncOpenAI
from config import config
import logging
from typing import List, Dict

class OpenAIService:
    """
    Сервис для работы с OpenAI API
    Обеспечивает взаимодействие с моделями GPT для генерации ответов
    """
    def __init__(self):
        """
        Инициализация сервиса OpenAI
        Создает клиент с API ключом и устанавливает максимальное количество токенов
        """
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.max_tokens = config.MAX_TOKENS

    async def get_chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Получение ответа от модели GPT
        Args:
            messages: Список сообщений в формате OpenAI
        Returns:
            str: Сгенерированный ответ или сообщение об ошибке
        """
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.7  # Параметр креативности ответов
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Ошибка OpenAI API: {str(e)}")
            return "Извините, произошла ошибка при обработке запроса."

    def format_messages(self, chat_history: List[Dict]) -> List[Dict[str, str]]:
        """
        Форматирование истории чата для OpenAI API
        Преобразует сообщения из базы данных в формат, понятный API
        Args:
            chat_history: История сообщений из базы данных
        Returns:
            List[Dict[str, str]]: Отформатированные сообщения
        """
        formatted_messages = []
        for msg in chat_history:
            # Определяем роль отправителя сообщения
            role = "user" if msg.is_from_user else "assistant"
            formatted_messages.append({
                "role": role,
                "content": msg.message
            })
        return formatted_messages

# Создание глобального экземпляра сервиса
openai_service = OpenAIService() 