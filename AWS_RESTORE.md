# Восстановление интеграции с AWS

## Обзор
Этот документ описывает процесс восстановления интеграции с AWS S3 для облачного хранения файлов в проекте.

## Шаги по восстановлению

1. Установите зависимость boto3:
```bash
pip install boto3==1.34.34
```

2. Добавьте следующие переменные окружения в файл `.env`:
```
AWS_ACCESS_KEY_ID=ваш_ключ_доступа
AWS_SECRET_ACCESS_KEY=ваш_секретный_ключ
AWS_REGION=ваш_регион
S3_BUCKET=имя_вашего_бакета
```

3. Замените файл `services/cloud_storage.py` на `services/cloud_storage_aws.py`:
```bash
mv services/cloud_storage_aws.py services/cloud_storage.py
```

4. Обновите конфигурацию в `config.py`, добавив следующие настройки:
```python
# Настройки облачного хранилища
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET")
```

5. Обновите `requirements.txt`, добавив:
```
boto3==1.34.34
```

## Миграция данных

Если у вас есть данные в локальном хранилище, которые нужно перенести в AWS S3:

1. Убедитесь, что у вас есть доступ к AWS S3 и создан бакет
2. Запустите скрипт миграции:
```python
import asyncio
from services.cloud_storage import cloud_storage
import os

async def migrate_to_aws():
    # Получаем список всех файлов в локальном хранилище
    files = await cloud_storage.list_files()
    
    # Загружаем каждый файл в S3
    for file in files:
        local_path = os.path.join(cloud_storage.files_dir, file)
        await cloud_storage.upload_file(local_path, file)
        print(f"Migrated: {file}")

if __name__ == "__main__":
    asyncio.run(migrate_to_aws())
```

## Проверка работоспособности

После восстановления интеграции проверьте:

1. Загрузку файла:
```python
await cloud_storage.upload_file("test.txt")
```

2. Скачивание файла:
```python
await cloud_storage.download_file("test.txt", "downloaded_test.txt")
```

3. Список файлов:
```python
files = await cloud_storage.list_files()
print(files)
```

## Примечания

- Убедитесь, что у вас есть необходимые права доступа к AWS S3
- Проверьте настройки безопасности бакета
- Рекомендуется использовать IAM роли с минимально необходимыми правами
- Храните учетные данные AWS в безопасном месте
- Регулярно обновляйте ключи доступа 