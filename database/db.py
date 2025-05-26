from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from .models import Base
from config import config
import logging
import asyncio
import contextlib

# Создание асинхронного движка базы данных
# Использует SQLite с асинхронным драйвером aiosqlite
engine = create_async_engine(
    f"sqlite+aiosqlite:///{config.DB_PATH}",
    echo=True,  # Включение логирования SQL-запросов
    future=True # Использование будущих фич SQLAlchemy
)

# Создание фабрики сессий для работы с базой данных
# expire_on_commit=False предотвращает автоматическое истечение объектов после коммита
async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def init_db():
    """
    Инициализация базы данных
    Создает все таблицы, определенные в моделях
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logging.info("База данных успешно инициализирована")
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {str(e)}")
        raise

@contextlib.asynccontextmanager
async def get_session() -> AsyncSession:
    """
    Получение сессии базы данных с использованием контекстного менеджера
    
    Возвращает:
        AsyncSession: Асинхронная сессия для работы с базой данных
        
    Пример использования:
        async with get_session() as session:
            result = await session.execute(...)
    """
    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close() 