from .context import Context


class Policy:
    """Политика для управления стратегией сортировки"""

    # Атрибут класса для тестов
    context = None

    def __init__(self, context):
        """
        Конструктор политики
        :param context: объект контекста
        """
        self.context = context

    def configure(self, algorithm=None):
        """
        Настраивает алгоритм сортировки в контексте
        :param algorithm: стратегия сортировки (опционально)
        :return: установленная стратегия
        """
        if algorithm is not None:
            self.context.sorting_algorithm = algorithm
        else:
            # Автоматический выбор стратегии на основе размера списка
            self.context.sorting_algorithm = self._choose_strategy()

        return self.context.sorting_algorithm

    def _choose_strategy(self):
        """
        Выбирает стратегию сортировки на основе размера списка
        :return: экземпляр стратегии сортировки
        """
        try:
            from assignment.sort_algorithms import BubbleSort, MergeSort
        except ImportError:
            try:
                from .sort_algorithms import BubbleSort, MergeSort
            except ImportError:
                import sort_algorithms

                BubbleSort = sort_algorithms.BubbleSort
                MergeSort = sort_algorithms.MergeSort

        if self.context.numbers is None:
            return BubbleSort()

        list_size = len(self.context.numbers)

        # Для маленьких списков (<= 10) используем пузырьковую сортировку
        if list_size <= 10:
            return BubbleSort()
        # Для больших списков (> 10) используем сортировку слиянием
        else:
            return MergeSort()
