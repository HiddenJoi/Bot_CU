import pytest
import os
import shutil
import tempfile
from services.cloud_storage import CloudStorage

@pytest.fixture
def cloud_storage():
    """Фикстура для создания экземпляра CloudStorage"""
    return CloudStorage()

@pytest.fixture
def test_file():
    """Фикстура с тестовым файлом"""
    test_content = "Тестовое содержимое"
    test_file_path = "test_file.txt"
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)
    yield test_file_path
    if os.path.exists(test_file_path):
        os.remove(test_file_path)

@pytest.fixture
def test_binary_file():
    """Фикстура с тестовым бинарным файлом"""
    test_content = bytes([i % 256 for i in range(1000)])  # Создаем бинарные данные
    test_file_path = "test_binary.bin"
    with open(test_file_path, "wb") as f:
        f.write(test_content)
    yield test_file_path
    if os.path.exists(test_file_path):
        os.remove(test_file_path)

@pytest.fixture
def test_large_file():
    """Фикстура с большим тестовым файлом"""
    test_file_path = "test_large.txt"
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write("Тест" * 1000000)  # Создаем файл размером около 4MB
    yield test_file_path
    if os.path.exists(test_file_path):
        os.remove(test_file_path)

@pytest.fixture(autouse=True)
def cleanup_storage():
    """Фикстура для очистки хранилища после каждого теста"""
    yield
    if os.path.exists("storage"):
        shutil.rmtree("storage")

@pytest.mark.asyncio
async def test_upload_file(cloud_storage, test_file):
    """Тест загрузки файла в хранилище"""
    result = await cloud_storage.upload_file(test_file)
    assert result is True
    assert os.path.exists(os.path.join(cloud_storage.files_dir, os.path.basename(test_file)))

@pytest.mark.asyncio
async def test_upload_file_with_custom_name(cloud_storage, test_file):
    """Тест загрузки файла с пользовательским именем"""
    custom_name = "custom_file.txt"
    result = await cloud_storage.upload_file(test_file, custom_name)
    assert result is True
    assert os.path.exists(os.path.join(cloud_storage.files_dir, custom_name))

@pytest.mark.asyncio
async def test_upload_file_name_conflict(cloud_storage, test_file):
    """Тест загрузки файла с конфликтующим именем"""
    # Загружаем файл первый раз
    await cloud_storage.upload_file(test_file)
    
    # Изменяем содержимое файла
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("Новое содержимое")
    
    # Загружаем файл с тем же именем
    result = await cloud_storage.upload_file(test_file)
    assert result is True
    
    # Проверяем, что файл был перезаписан
    with open(os.path.join(cloud_storage.files_dir, os.path.basename(test_file)), "r", encoding="utf-8") as f:
        content = f.read()
    assert content == "Новое содержимое"

@pytest.mark.asyncio
async def test_upload_binary_file(cloud_storage, test_binary_file):
    """Тест загрузки бинарного файла"""
    result = await cloud_storage.upload_file(test_binary_file)
    assert result is True
    
    # Проверяем содержимое
    with open(os.path.join(cloud_storage.files_dir, os.path.basename(test_binary_file)), "rb") as f:
        content = f.read()
    assert len(content) == 1000
    assert all(content[i] == i % 256 for i in range(1000))

@pytest.mark.asyncio
async def test_upload_large_file(cloud_storage, test_large_file):
    """Тест загрузки большого файла"""
    result = await cloud_storage.upload_file(test_large_file)
    assert result is True
    
    # Проверяем размер загруженного файла
    uploaded_file = os.path.join(cloud_storage.files_dir, os.path.basename(test_large_file))
    assert os.path.exists(uploaded_file)
    assert os.path.getsize(uploaded_file) > 1024 * 1024  # Больше 1MB

@pytest.mark.asyncio
async def test_download_file(cloud_storage, test_file):
    """Тест скачивания файла из хранилища"""
    # Сначала загружаем файл
    await cloud_storage.upload_file(test_file)
    
    # Затем скачиваем его в новое место
    download_path = "downloaded_file.txt"
    result = await cloud_storage.download_file(os.path.basename(test_file), download_path)
    
    assert result is True
    assert os.path.exists(download_path)
    
    # Проверяем содержимое
    with open(download_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == "Тестовое содержимое"
    
    # Очистка
    os.remove(download_path)

@pytest.mark.asyncio
async def test_download_file_permissions(cloud_storage, test_file):
    """Тест скачивания файла с проверкой прав доступа"""
    await cloud_storage.upload_file(test_file)
    
    # Создаем директорию без прав на запись
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chmod(temp_dir, 0o444)  # Только чтение
        
        download_path = os.path.join(temp_dir, "downloaded_file.txt")
        result = await cloud_storage.download_file(os.path.basename(test_file), download_path)
        assert result is False  # Должно вернуть False из-за отсутствия прав

@pytest.mark.asyncio
async def test_list_files(cloud_storage, test_file):
    """Тест получения списка файлов"""
    # Загружаем несколько файлов
    await cloud_storage.upload_file(test_file)
    await cloud_storage.upload_file(test_file, "test_file2.txt")
    
    # Получаем список файлов
    files = await cloud_storage.list_files()
    assert len(files) >= 2
    assert os.path.basename(test_file) in files
    assert "test_file2.txt" in files

@pytest.mark.asyncio
async def test_list_files_with_prefix(cloud_storage, test_file):
    """Тест получения списка файлов с префиксом"""
    # Загружаем файлы с разными именами
    await cloud_storage.upload_file(test_file, "test_1.txt")
    await cloud_storage.upload_file(test_file, "other_1.txt")
    
    # Получаем список файлов с префиксом
    files = await cloud_storage.list_files(prefix="test_")
    assert len(files) == 1
    assert "test_1.txt" in files

@pytest.mark.asyncio
async def test_delete_file(cloud_storage, test_file):
    """Тест удаления файла"""
    # Загружаем файл
    await cloud_storage.upload_file(test_file)
    file_name = os.path.basename(test_file)
    
    # Удаляем файл
    result = await cloud_storage.delete_file(file_name)
    assert result is True
    assert not os.path.exists(os.path.join(cloud_storage.files_dir, file_name))

@pytest.mark.asyncio
async def test_delete_nonexistent_file(cloud_storage):
    """Тест удаления несуществующего файла"""
    result = await cloud_storage.delete_file("nonexistent.txt")
    assert result is True  # Должен вернуть True, так как файл не существует

def test_storage_directories_creation(cloud_storage):
    """Тест создания директорий хранилища"""
    assert os.path.exists(cloud_storage.storage_dir)
    assert os.path.exists(cloud_storage.backups_dir)
    assert os.path.exists(cloud_storage.files_dir)
    
    # Проверяем права доступа к директориям
    assert os.access(cloud_storage.storage_dir, os.W_OK)
    assert os.access(cloud_storage.backups_dir, os.W_OK)
    assert os.access(cloud_storage.files_dir, os.W_OK) 