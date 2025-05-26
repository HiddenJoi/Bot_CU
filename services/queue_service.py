from celery import Celery
from config import config
import logging
from typing import Any, Dict

# Инициализация Celery для асинхронной обработки задач
# Использует Redis в качестве брокера сообщений и хранилища результатов
celery = Celery(
    'bank_bot',
    broker=config.CELERY_BROKER_URL,
    backend=config.REDIS_URL
)

@celery.task
def send_broadcast_message(user_ids: list, message: str) -> Dict[str, Any]:
    """
    Отправляет сообщение множеству пользователей через очередь задач
    Args:
        user_ids: Список ID пользователей для рассылки
        message: Текст сообщения для отправки
    Returns:
        Dict[str, Any]: Результаты отправки с списками успешных и неудачных отправок
    """
    import asyncio
    from aiogram import Bot
    
    results = {
        'success': [],
        'failed': []
    }
    
    async def send_messages():
        bot = Bot(token=config.BOT_TOKEN)
        for user_id in user_ids:
            try:
                await bot.send_message(user_id, message)
                results['success'].append(user_id)
            except Exception as e:
                logging.error(f"Ошибка при отправке сообщения пользователю {user_id}: {str(e)}")
                results['failed'].append(user_id)
        await bot.session.close()
    
    asyncio.run(send_messages())
    return results

@celery.task
def process_moderator_notification(user_id: int, message: str) -> None:
    """
    Обрабатывает уведомление модераторов о новом запросе пользователя
    Args:
        user_id: ID пользователя, отправившего запрос
        message: Текст запроса пользователя
    """
    import asyncio
    from aiogram import Bot
    from database.queries import get_all_users
    
    async def notify_moderators():
        bot = Bot(token=config.BOT_TOKEN)
        
        # Получаем список всех пользователей
        all_users = await get_all_users()
        
        # Фильтруем модераторов
        moderators = [user for user in all_users if user.role == "MODERATOR"]
        
        for moderator in moderators:
            try:
                notification = f"Новый запрос от пользователя {user_id}:\n{message}"
                await bot.send_message(moderator.telegram_id, notification)
            except Exception as e:
                logging.error(f"Ошибка при уведомлении модератора {moderator.telegram_id}: {str(e)}")
        
        await bot.session.close()
    
    asyncio.run(notify_moderators())

@celery.task
def backup_database() -> None:
    """
    Создает резервную копию базы данных и загружает её в облачное хранилище
    Имя файла бэкапа содержит дату и время создания
    """
    import asyncio
    import shutil
    from datetime import datetime
    from services.cloud_storage import cloud_storage
    
    # Создание имени файла бэкапа с временной меткой
    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    # Копирование файла базы данных
    shutil.copy2(config.DB_PATH, backup_name)
    
    async def upload_backup():
        try:
            # Загрузка бэкапа в облачное хранилище
            await cloud_storage.upload_file(backup_name, f"backups/{backup_name}")
        except Exception as e:
            logging.error(f"Ошибка при загрузке бэкапа: {str(e)}")
    
    asyncio.run(upload_backup())

@celery.task
def process_audit_log(event_type: str, user_id: int, details: Dict[str, Any]) -> None:
    """
    Обрабатывает запись в лог аудита в асинхронном режиме
    Args:
        event_type: Тип события аудита
        user_id: ID пользователя
        details: Дополнительные детали события
    """
    import asyncio
    
    async def add_log():
        from database.queries import add_audit_log
        await add_audit_log(event_type, user_id, details)
    
    try:
        asyncio.run(add_log())
    except Exception as e:
        logging.error(f"Ошибка при добавлении аудит-лога: {str(e)}")

# Настройки Celery для оптимизации работы
celery.conf.update(
    task_serializer='json',          # Сериализация задач в JSON
    accept_content=['json'],         # Прием только JSON контента
    result_serializer='json',        # Сериализация результатов в JSON
    timezone='Europe/Moscow',        # Часовой пояс
    enable_utc=True,                 # Использование UTC времени
    task_track_started=True,         # Отслеживание начала выполнения задач
    task_time_limit=300,            # Максимальное время выполнения задачи (5 минут)
    worker_max_tasks_per_child=1000  # Максимальное количество задач на воркер
) 