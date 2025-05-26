import boto3
from botocore.exceptions import ClientError
from config import config
import logging
from typing import Optional
import os

class CloudStorage:
    """
    Сервис для работы с облачным хранилищем S3
    Обеспечивает загрузку, скачивание и управление файлами в AWS S3
    """
    def __init__(self):
        """
        Инициализация клиента S3
        Создает подключение к AWS с использованием учетных данных из конфигурации
        """
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )
        self.bucket = config.S3_BUCKET  # Имя S3 бакета для хранения файлов

    async def upload_file(self, file_path: str, object_name: Optional[str] = None) -> bool:
        """
        Загружает файл в S3 бакет
        Args:
            file_path: Путь к файлу на локальной машине
            object_name: Имя объекта в S3 (если не указано, используется имя файла)
        Returns:
            bool: True если загрузка успешна, иначе False
        """
        if object_name is None:
            object_name = os.path.basename(file_path)

        try:
            self.s3_client.upload_file(file_path, self.bucket, object_name)
            return True
        except ClientError as e:
            logging.error(f"Ошибка при загрузке файла {file_path}: {str(e)}")
            return False

    async def download_file(self, object_name: str, file_path: str) -> bool:
        """
        Скачивает файл из S3 бакета
        Args:
            object_name: Имя объекта в S3
            file_path: Путь для сохранения файла на локальной машине
        Returns:
            bool: True если скачивание успешно, иначе False
        """
        try:
            self.s3_client.download_file(self.bucket, object_name, file_path)
            return True
        except ClientError as e:
            logging.error(f"Ошибка при скачивании файла {object_name}: {str(e)}")
            return False

    async def list_files(self, prefix: str = '') -> list:
        """
        Получает список файлов в S3 бакете
        Args:
            prefix: Префикс для фильтрации файлов
        Returns:
            list: Список имен объектов в бакете
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except ClientError as e:
            logging.error(f"Ошибка при получении списка файлов: {str(e)}")
            return []

    async def delete_file(self, object_name: str) -> bool:
        """
        Удаляет файл из S3 бакета
        Args:
            object_name: Имя объекта для удаления
        Returns:
            bool: True если удаление успешно, иначе False
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=object_name)
            return True
        except ClientError as e:
            logging.error(f"Ошибка при удалении файла {object_name}: {str(e)}")
            return False

# Создание глобального экземпляра сервиса
cloud_storage = CloudStorage()

async def upload_to_cloud(file_path: str, object_name: Optional[str] = None) -> bool:
    """
    Вспомогательная функция для загрузки файла в облако
    Упрощает использование сервиса CloudStorage
    Args:
        file_path: Путь к файлу на локальной машине
        object_name: Имя объекта в S3 (опционально)
    Returns:
        bool: Результат операции загрузки
    """
    return await cloud_storage.upload_file(file_path, object_name) 