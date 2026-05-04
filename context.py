class Context:
    """Контекст для паттерна Стратегия"""

    # Атрибуты класса для тестов
    numbers = None
    sorting_algorithm = None

    def __init__(self):
        self.numbers = []  # Список чисел для сортировки
        self.sorting_algorithm = None  # Текущая стратегия сортировки

    def sort(self):
        """
        Выполняет сортировку с использованием текущей стратегии
        :return: отсортированный список
        """
        if self.sorting_algorithm is None:
            raise ValueError("Стратегия сортировки не установлена")

        if self.numbers is None:
            return None

        # Вызываем perform_sort, который изменит self.numbers
        self.sorting_algorithm.perform_sort(self.numbers)
        return self.numbers
