from abc import ABC, abstractmethod


class SortStrategy(ABC):
    """Абстрактный базовый класс для стратегий сортировки"""

    @abstractmethod
    def perform_sort(self, data):
        """
        Выполняет сортировку данных
        :param data: список для сортировки
        :return: отсортированный список
        """
        pass
