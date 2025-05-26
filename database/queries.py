from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from .models import User, ChatHistory
from datetime import datetime
import logging
from .db import get_session

async def create_user(telegram_id: int, phone_number: str, role: str = "user") -> User:
    """
    Создает нового пользователя в базе данных
    Args:
        telegram_id: Telegram ID пользователя
        phone_number: Номер телефона пользователя
        role: Роль пользователя (по умолчанию 'user')
    Returns:
        User: Созданный пользователь
    """
    async with get_session() as session:
        user = User(
            telegram_id=telegram_id,
            phone_number=phone_number,
            role=role
        )
        session.add(user)
        await session.commit()
        return user

async def get_user_by_telegram_id(telegram_id: int) -> User:
    """
    Получает пользователя по Telegram ID
    Args:
        telegram_id: Telegram ID пользователя
    Returns:
        User: Найденный пользователь или None
    """
    async with get_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

async def update_user_last_message(telegram_id: int):
    """
    Обновляет время последнего сообщения пользователя
    Args:
        telegram_id: Telegram ID пользователя
    """
    async with get_session() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(last_message_date=datetime.now())
        )
        await session.commit()

async def add_chat_message(user_id: int, message: str, is_from_user: bool, is_moderator_chat: bool = False):
    """
    Добавляет сообщение в историю чата
    Args:
        user_id: ID пользователя
        message: Текст сообщения
        is_from_user: Отправлено ли сообщение пользователем
        is_moderator_chat: Является ли сообщение частью чата с модератором
    """
    async with get_session() as session:
        chat_message = ChatHistory(
            user_id=user_id,
            message=message,
            is_from_user=is_from_user,
            is_moderator_chat=is_moderator_chat
        )
        session.add(chat_message)
        await session.commit()

async def get_last_messages(user_id: int, limit: int = 5) -> list:
    """
    Получает последние сообщения пользователя
    Args:
        user_id: ID пользователя
        limit: Максимальное количество сообщений
    Returns:
        list: Список последних сообщений
    """
    async with get_session() as session:
        result = await session.execute(
            select(ChatHistory)
            .where(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.timestamp.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))

async def get_all_users() -> list:
    """
    Получает список всех пользователей
    Returns:
        list: Список всех пользователей
    """
    async with get_session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()

async def update_user_moderator_chat_status(telegram_id: int, status: bool):
    """
    Обновляет статус чата пользователя с модератором
    Args:
        telegram_id: Telegram ID пользователя
        status: Новый статус
    """
    async with get_session() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_chatting_with_moderator=status)
        )
        await session.commit() 