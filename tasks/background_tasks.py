from typing import Any
import asyncio
from datetime import datetime, timedelta
from database.queries import get_session
from database.models import ChatHistory, User
from sqlalchemy import delete, update
import logging
from services.cloud_storage import cloud_storage
import os

async def cleanup_old_data() -> None:
    """
    Периодическая очистка устаревших данных
    Удаляет неактуальные записи из базы данных и кэша
    """
    while True:
        try:
            async with get_session() as session:
                # Удаление старых сообщений (старше 30 дней)
                thirty_days_ago = datetime.now() - timedelta(days=30)
                await session.execute(
                    delete(ChatHistory).where(ChatHistory.timestamp < thirty_days_ago)
                )
                
                # Деактивация неактивных пользователей (не было сообщений 90 дней)
                ninety_days_ago = datetime.now() - timedelta(days=90)
                await session.execute(
                    update(User)
                    .where(User.last_message_date < ninety_days_ago)
                    .values(is_active=False)
                )
                
                await session.commit()
                
                # Архивация логов
                log_dir = "logs"
                if os.path.exists(log_dir):
                    for filename in os.listdir(log_dir):
                        if filename.endswith(".log"):
                            file_path = os.path.join(log_dir, filename)
                            # Проверяем возраст файла
                            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_age.days > 7:  # Архивируем логи старше 7 дней
                                # Загружаем лог в облачное хранилище
                                archive_name = f"logs/archive/{filename}.{datetime.now().strftime('%Y%m%d')}"
                                await cloud_storage.upload_file(file_path, archive_name)
                                # Удаляем локальный файл после архивации
                                os.remove(file_path)
                
                logging.info("Очистка старых данных выполнена успешно")
                
            await asyncio.sleep(86400)  # Запуск раз в сутки (24 часа)
        except Exception as e:
            logging.error(f"Ошибка при выполнении задачи очистки: {e}")
            await asyncio.sleep(300)  # При ошибке ждем 5 минут перед повторной попыткой

async def start_background_tasks() -> None:
    """
    Запуск всех фоновых задач
    Собирает все задачи в список и запускает их параллельно
    """
    tasks = [
        cleanup_old_data(),
        # Здесь можно добавить другие фоновые задачи:
        # - Проверка состояния сервисов
        # - Синхронизация данных
        # - Отправка уведомлений
    ]
    await asyncio.gather(*tasks) 