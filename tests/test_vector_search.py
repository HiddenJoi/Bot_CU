import pytest
from services.vector_search import VectorSearch
from config import config

@pytest.fixture
def vector_search():
    """Фикстура для создания экземпляра VectorSearch"""
    return VectorSearch()

@pytest.fixture
def test_contexts():
    """Фикстура с тестовыми контекстами"""
    return [
        "Как открыть вклад в банке? Для открытия вклада нужно прийти в отделение с паспортом.",
        "Как пополнить карту? Пополнение возможно через банкомат или мобильное приложение.",
        "Как получить кредит? Для получения кредита нужна справка о доходах и паспорт."
    ]

def test_initialization(vector_search):
    """Тест инициализации сервиса векторного поиска"""
    assert vector_search.model is not None
    assert vector_search.index is None
    assert vector_search.contexts == []
    assert vector_search.threshold == config.SIMILARITY_THRESHOLD

def test_build_index(vector_search, test_contexts):
    """Тест построения индекса"""
    vector_search.build_index(test_contexts)
    assert vector_search.index is not None
    assert len(vector_search.contexts) == len(test_contexts)
    assert vector_search.contexts == test_contexts

def test_search_exact_match(vector_search, test_contexts):
    """Тест поиска точного совпадения"""
    vector_search.build_index(test_contexts)
    query = "Как открыть вклад в банке?"
    result, distance = vector_search.search(query)
    assert result is not None
    assert result == test_contexts[0]
    assert distance < vector_search.threshold

def test_search_similar_match(vector_search, test_contexts):
    """Тест поиска похожего совпадения"""
    vector_search.build_index(test_contexts)
    query = "Хочу открыть депозит, что нужно?"
    result, distance = vector_search.search(query)
    assert result is not None
    assert result == test_contexts[0]
    assert distance < vector_search.threshold

def test_search_no_match(vector_search, test_contexts):
    """Тест поиска без совпадений"""
    vector_search.build_index(test_contexts)
    query = "Как купить акции на бирже?"
    result, distance = vector_search.search(query)
    assert result is None
    assert distance > vector_search.threshold

def test_search_empty_index(vector_search):
    """Тест поиска с пустым индексом"""
    query = "Как открыть вклад?"
    result, distance = vector_search.search(query)
    assert result is None
    assert distance == 0.0

def test_search_threshold(vector_search, test_contexts):
    """Тест работы порога схожести"""
    vector_search.build_index(test_contexts)
    # Устанавливаем очень низкий порог схожести
    vector_search.threshold = 0.1
    query = "Как купить акции?"
    result, distance = vector_search.search(query)
    assert result is None
    assert distance > vector_search.threshold 