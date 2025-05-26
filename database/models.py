from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

# Базовый класс для всех моделей базы данных
Base = declarative_base()

class User(Base):
    """
    Модель пользователя в системе.
    
    Атрибуты:
        id (int): Уникальный идентификатор пользователя в базе данных
        telegram_id (int): Уникальный идентификатор пользователя в Telegram
        phone_number (str): Номер телефона пользователя
        role (str): Роль пользователя в системе (user/moderator/admin)
        registration_date (datetime): Дата и время регистрации пользователя
        last_message_date (datetime): Дата и время последнего сообщения от пользователя
        is_active (bool): Статус активности пользователя
        is_chatting_with_moderator (bool): Флаг, указывающий на то, что пользователь находится в чате с модератором
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    phone_number = Column(String, nullable=False)
    role = Column(String, nullable=False, default='user')
    registration_date = Column(DateTime, default=func.now())
    last_message_date = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    is_chatting_with_moderator = Column(Boolean, default=False)

class ChatHistory(Base):
    """
    Модель истории сообщений в чате.
    
    Атрибуты:
        id (int): Уникальный идентификатор сообщения
        user_id (int): Идентификатор пользователя, отправившего сообщение
        message (str): Текст сообщения
        is_from_user (bool): Флаг, указывающий, отправлено ли сообщение пользователем
        timestamp (datetime): Дата и время отправки сообщения
        is_moderator_chat (bool): Флаг, указывающий, является ли сообщение частью чата с модератором
    """
    __tablename__ = 'chat_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    message = Column(String, nullable=False)
    is_from_user = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    is_moderator_chat = Column(Boolean, default=False) 