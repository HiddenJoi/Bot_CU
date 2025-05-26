import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import config
from handlers import user_handlers, moderator_handlers
from database.db import init_db
from services.vector_search import vector_search
from middlewares.auth_middleware import AuthMiddleware
from tasks.background_tasks import start_background_tasks

# Настройка системы логирования
# Формат логов: дата-время - имя логгера - уровень - сообщение
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=config.LOG_FILE,
    encoding='utf-8'  # Добавляем явное указание кодировки UTF-8
)

async def main():
    try:
        # Инициализация базы данных
        # Создание необходимых таблиц и подключение к БД
        logging.info("Инициализация базы данных...")
        await init_db()
        logging.info("База данных успешно инициализирована")

        # Инициализация бота и диспетчера
        # Создание экземпляра бота с токеном из конфигурации
        if not config.BOT_TOKEN:
            logging.critical("Не указан BOT_TOKEN. Бот не может быть запущен.")
            return
        
        bot = Bot(token=config.BOT_TOKEN)
        dp = Dispatcher()
        
        # Регистрация middleware
        logging.info("Регистрация middleware...")
        dp.update.middleware.register(AuthMiddleware())
        
        # Регистрация обработчиков сообщений
        # Подключение роутеров для пользователей и модераторов
        logging.info("Регистрация обработчиков сообщений...")
        dp.include_router(user_handlers.router)
        dp.include_router(moderator_handlers.router)

        # Загрузка контекстного файла для векторного поиска
        # Файл содержит информацию для поиска похожих вопросов
        try:
            logging.info("Загрузка контекстного файла...")
            with open(config.CONTEXT_FILE, 'r', encoding='utf-8') as f:
                contexts = f.read().split('\n\n')
                vector_search.build_index(contexts)
            logging.info(f"Загружено {len(contexts)} контекстов для векторного поиска")
        except FileNotFoundError:
            logging.warning(f"Контекстный файл не найден: {config.CONTEXT_FILE}")
        except Exception as e:
            logging.error(f"Ошибка при загрузке контекстного файла: {str(e)}")
        
        # Запуск фоновых задач
        logging.info("Запуск фоновых задач...")
        asyncio.create_task(start_background_tasks())
        
        # Запуск бота в режиме long polling
        # Бот начинает принимать и обрабатывать сообщения
        logging.info("Запуск бота...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.critical(f"Критическая ошибка при запуске бота: {str(e)}")
        raise

if __name__ == '__main__':
    # Запуск асинхронной функции main
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")
    except Exception as e:
        logging.critical(f"Необработанная ошибка: {str(e)}")
        raise 