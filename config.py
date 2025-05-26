import os
from dotenv import load_dotenv
from typing import Dict, List

# Загрузка переменных окружения из файла .env
load_dotenv()

class Config:
    # Основные настройки бота
    # Токен для доступа к API Telegram
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    # Ключ для доступа к API OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # Путь к файлу базы данных SQLite
    DB_PATH = os.getenv("DB_PATH", "bank_bot.db")
    # Путь к файлу логов
    LOG_FILE = os.getenv("LOG_FILE", "bot.log")
    # Порог схожести для векторного поиска (0.0 - 1.0)
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    # Максимальное количество токенов для генерации ответа
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1500"))
    # Путь к файлу с контекстной информацией
    CONTEXT_FILE = os.getenv("CONTEXT_FILE", "context.txt")
    
    # Настройки очередей задач
    # URL для подключения к Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    # URL для брокера Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    
    # Настройки локального хранилища
    # Путь к директории для хранения файлов
    STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
    # Путь к директории для бэкапов
    BACKUPS_DIR = os.getenv("BACKUPS_DIR", "storage/backups")
    # Путь к директории для файлов
    FILES_DIR = os.getenv("FILES_DIR", "storage/files")
    
    # Настройки мониторинга
    # Порт для метрик Prometheus
    PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9090"))
    # Endpoint для отправки трейсов в Jaeger
    JAEGER_ENDPOINT = os.getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
    
    # Настройки ограничения запросов
    # Максимальное количество сообщений в минуту
    RATE_LIMIT = int(os.getenv("RATE_LIMIT", "10"))
    # Временное окно для ограничения в секундах
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Роли пользователей и их разрешения
    # Определяет, какие действия доступны каждой роли
    ROLES: Dict[str, List[str]] = {
        "USER": ["read_messages", "send_messages"],
        "MODERATOR": ["read_messages", "send_messages", "view_users", "send_broadcast"],
        "ADMIN": ["read_messages", "send_messages", "view_users", "send_broadcast", 
                 "manage_roles", "view_logs", "manage_settings"]
    }
    
    # Шаблоны сообщений бота
    # Тексты сообщений для различных ситуаций
    MESSAGES = {
        "WELCOME": "Добро пожаловать! Пожалуйста, поделитесь своим номером телефона для регистрации.",
        "REGISTRATION_SUCCESS": "Регистрация успешно завершена!",
        "MODERATOR_TRANSFER": "Ваш запрос передан модератору. Ожидайте ответа.",
        "CHAT_ENDED": "Диалог завершен.",
        "BROADCAST_SENT": "Рассылка отправлена успешно.",
        "HELP_REQUEST": "Ваш запрос передан модератору.",
        "RATE_LIMIT_EXCEEDED": "Слишком много запросов. Пожалуйста, подождите.",
        "PERMISSION_DENIED": "У вас нет прав для выполнения этой операции."
    }
    
    # Слоты контекста диалога
    # Переменные, которые сохраняются в контексте диалога
    CONTEXT_SLOTS = [
        "user_name",        # Имя пользователя
        "card_number",      # Номер карты
        "request_type",     # Тип запроса
        "last_operation",   # Последняя операция
        "preferred_language" # Предпочитаемый язык
    ]
    
    # События аудита
    # Типы событий, которые логируются в системе
    AUDIT_EVENTS = {
        "USER_REGISTERED": "user_registered",      # Регистрация пользователя
        "MESSAGE_SENT": "message_sent",            # Отправка сообщения
        "MODERATOR_ASSIGNED": "moderator_assigned", # Назначение модератора
        "ROLE_CHANGED": "role_changed",            # Изменение роли
        "SETTINGS_CHANGED": "settings_changed"     # Изменение настроек
    }

# Создание экземпляра конфигурации
config = Config() 