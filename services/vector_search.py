import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
import logging
from config import config

class VectorSearch:
    """
    Сервис для векторного поиска похожих контекстов
    Использует FAISS для эффективного поиска и SentenceTransformer для эмбеддингов
    """
    def __init__(self):
        """
        Инициализация сервиса векторного поиска
        Загружает модель для создания эмбеддингов и устанавливает порог схожести
        """
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Модель для создания эмбеддингов
        self.index = None  # FAISS индекс для быстрого поиска
        self.contexts = []  # Список контекстов
        self.threshold = config.SIMILARITY_THRESHOLD  # Порог схожести для фильтрации результатов

    def build_index(self, contexts: List[str]):
        """
        Построение FAISS индекса из контекстов
        Создает векторные представления текстов и строит индекс для быстрого поиска
        Args:
            contexts: Список текстовых контекстов
        """
        self.contexts = contexts
        # Создание эмбеддингов для всех контекстов
        embeddings = self.model.encode(contexts)
        dimension = embeddings.shape[1]
        # Создание и заполнение FAISS индекса
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))

    def search(self, query: str) -> Tuple[str, float]:
        """
        Поиск наиболее релевантного контекста
        Args:
            query: Поисковый запрос
        Returns:
            Tuple[str, float]: Найденный контекст и его оценка схожести
        """
        if not self.index:
            return None, 0.0

        # Создание эмбеддинга для запроса
        query_embedding = self.model.encode([query])
        # Поиск ближайшего соседа
        distances, indices = self.index.search(query_embedding.astype('float32'), 1)
        
        # Проверка на соответствие порогу схожести
        if distances[0][0] > self.threshold:
            return None, distances[0][0]
        
        # Возврат найденного контекста и его оценки
        return self.contexts[indices[0][0]], distances[0][0]

# Создание глобального экземпляра сервиса
vector_search = VectorSearch() 