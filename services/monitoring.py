from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from prometheus_client import Counter, Histogram, start_http_server
from config import config
import logging
from typing import Dict, Any
import time

# Инициализация системы трассировки
# Создает провайдер трейсов с именем сервиса
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({"service.name": "bank_bot"})
    )
)

# Настройка экспортера для отправки трейсов в Jaeger
# Использует локальный агент Jaeger для сбора данных
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Определение метрик Prometheus для мониторинга
messages_counter = Counter('bot_messages_total', 'Общее количество обработанных сообщений')
message_processing_time = Histogram('message_processing_seconds', 'Время обработки сообщений')
error_counter = Counter('bot_errors_total', 'Общее количество ошибок')
user_actions = Counter('user_actions_total', 'Общее количество действий пользователей', ['action_type'])

class MonitoringService:
    """
    Сервис для мониторинга и трассировки
    Обеспечивает сбор метрик, трейсов и аудит событий
    """
    def __init__(self):
        """
        Инициализация сервиса мониторинга
        Создает трейсер для трассировки операций
        """
        self.tracer = trace.get_tracer(__name__)

    def start_server(self):
        """
        Запускает HTTP сервер для метрик Prometheus
        Метрики доступны на порту, указанном в конфигурации
        """
        start_http_server(config.PROMETHEUS_PORT)

    def track_message(self, message_type: str, processing_time: float = None):
        """
        Отслеживает обработку сообщения
        Args:
            message_type: Тип обработанного сообщения
            processing_time: Время обработки в секундах (опционально)
        """
        messages_counter.inc()
        if processing_time is not None:
            message_processing_time.observe(processing_time)
        user_actions.labels(action_type=message_type).inc()

    def track_error(self, error_type: str):
        """
        Отслеживает возникновение ошибок
        Args:
            error_type: Тип произошедшей ошибки
        """
        error_counter.inc()
        user_actions.labels(action_type=f"error_{error_type}").inc()

    def create_span(self, name: str, attributes: Dict[str, Any] = None):
        """
        Создает новый span для трассировки операции
        Args:
            name: Имя операции
            attributes: Дополнительные атрибуты для span
        Returns:
            Span: Созданный span для трассировки
        """
        return self.tracer.start_span(name, attributes=attributes)

    def log_audit_event(self, event_type: str, user_id: int, details: Dict[str, Any]):
        """
        Логирует событие аудита с трассировкой
        Args:
            event_type: Тип события аудита
            user_id: ID пользователя
            details: Дополнительные детали события
        """
        with self.create_span("audit_event") as span:
            span.set_attribute("event_type", event_type)
            span.set_attribute("user_id", user_id)
            for key, value in details.items():
                span.set_attribute(key, str(value))
            logging.info(f"Событие аудита: {event_type}, Пользователь: {user_id}, Детали: {details}")

# Создание глобального экземпляра сервиса мониторинга
monitoring = MonitoringService()

def track_execution_time(func):
    """
    Декоратор для отслеживания времени выполнения функции
    Args:
        func: Функция, время выполнения которой нужно отслеживать
    Returns:
        wrapper: Обернутая функция с мониторингом времени выполнения
    """
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            processing_time = time.time() - start_time
            monitoring.track_message(func.__name__, processing_time)
            return result
        except Exception as e:
            monitoring.track_error(type(e).__name__)
            raise
    return wrapper 