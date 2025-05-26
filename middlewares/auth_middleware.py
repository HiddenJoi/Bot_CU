from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from database.queries import get_user_by_telegram_id
from config import config
import logging

class AuthMiddleware(BaseMiddleware):
    """
    Middleware для аутентификации пользователей
    Проверяет права доступа и авторизацию перед обработкой сообщений
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Проверяем, является ли событие сообщением
        if not isinstance(event, Message):
            return await handler(event, data)

        # Получаем ID пользователя из сообщения
        user_id = event.from_user.id

        # Получаем пользователя из базы данных
        user = await get_user_by_telegram_id(user_id)

        # Проверяем команды, доступные без авторизации
        if event.text and event.text.startswith('/start'):
            return await handler(event, data)

        # Если пользователь не найден и это не команда /start
        if not user:
            await event.answer("Пожалуйста, зарегистрируйтесь с помощью команды /start")
            return

        # Проверяем активность пользователя
        if not user.is_active:
            await event.answer("Ваш аккаунт деактивирован. Обратитесь к администратору.")
            return

        # Проверяем права доступа для команд модератора
        if event.text and event.text.startswith('/broadcast'):
            if user.role != "MODERATOR":
                await event.answer(config.MESSAGES["PERMISSION_DENIED"])
                return

        # Добавляем информацию о пользователе в данные
        data['user'] = user

        # Продолжаем обработку сообщения
        return await handler(event, data) 