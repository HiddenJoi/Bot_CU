import os
import shutil
import logging
from typing import Optional
from config import config

class CloudStorage:
    """
    Сервис для работы с локальным хранилищем файлов
    Обеспечивает загрузку, скачивание и управление файлами в локальной файловой системе
    """
    def __init__(self):
        """
        Инициализация локального хранилища
        Создает необходимые директории для хранения файлов
        """
        self.storage_dir = os.path.join(os.getcwd(), "storage")
        self.backups_dir = os.path.join(self.storage_dir, "backups")
        self.files_dir = os.path.join(self.storage_dir, "files")
        
        # Создаем необходимые директории
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.backups_dir, exist_ok=True)
        os.makedirs(self.files_dir, exist_ok=True)

    async def upload_file(self, file_path: str, object_name: Optional[str] = None) -> bool:
        """
        Копирует файл в локальное хранилище
        Args:
            file_path: Путь к файлу на локальной машине
            object_name: Имя файла в хранилище (если не указано, используется имя файла)
        Returns:
            bool: True если копирование успешно, иначе False
        """
        if object_name is None:
            object_name = os.path.basename(file_path)
            
        target_path = os.path.join(self.files_dir, object_name)
        
        try:
            shutil.copy2(file_path, target_path)
            return True
        except Exception as e:
            logging.error(f"Ошибка при копировании файла {file_path}: {str(e)}")
            return False

    async def download_file(self, object_name: str, file_path: str) -> bool:
        """
        Копирует файл из локального хранилища
        Args:
            object_name: Имя файла в хранилище
            file_path: Путь для сохранения файла
        Returns:
            bool: True если копирование успешно, иначе False
        """
        source_path = os.path.join(self.files_dir, object_name)
        
        try:
            shutil.copy2(source_path, file_path)
            return True
        except Exception as e:
            logging.error(f"Ошибка при копировании файла {object_name}: {str(e)}")
            return False

    async def list_files(self, prefix: str = '') -> list:
        """
        Получает список файлов в локальном хранилище
        Args:
            prefix: Префикс для фильтрации файлов
        Returns:
            list: Список имен файлов
        """
        try:
            files = []
            for file in os.listdir(self.files_dir):
                if file.startswith(prefix):
                    files.append(file)
            return files
        except Exception as e:
            logging.error(f"Ошибка при получении списка файлов: {str(e)}")
            return []

    async def delete_file(self, object_name: str) -> bool:
        """
        Удаляет файл из локального хранилища
        Args:
            object_name: Имя файла для удаления
        Returns:
            bool: True если удаление успешно, иначе False
        """
        file_path = os.path.join(self.files_dir, object_name)
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            logging.error(f"Ошибка при удалении файла {object_name}: {str(e)}")
            return False

# Создание глобального экземпляра сервиса
cloud_storage = CloudStorage()

async def upload_to_cloud(file_path: str, object_name: Optional[str] = None) -> bool:
    """
    Вспомогательная функция для загрузки файла в хранилище
    Упрощает использование сервиса CloudStorage
    Args:
        file_path: Путь к файлу на локальной машине
        object_name: Имя файла в хранилище (опционально)
    Returns:
        bool: Результат операции загрузки
    """
    return await cloud_storage.upload_file(file_path, object_name) 