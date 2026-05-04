from .sort_strategy import SortStrategy


class BubbleSort(SortStrategy):
    """Сортировка пузырьком"""

    def perform_sort(self, data):
        """
        Реализация сортировки пузырьком (изменяет исходный список)
        :param data: список для сортировки
        :return: отсортированный список (тот же объект)
        """
        if data is None:
            return None

        n = len(data)

        for i in range(n):
            for j in range(0, n - i - 1):
                if data[j] > data[j + 1]:
                    data[j], data[j + 1] = data[j + 1], data[j]

        return data


class MergeSort(SortStrategy):
    """Сортировка слиянием"""

    def perform_sort(self, data):
        """
        Реализация сортировки слиянием (изменяет исходный список)
        :param data: список для сортировки
        :return: отсортированный список (тот же объект)
        """
        if data is None:
            return None

        if len(data) <= 1:
            return data

        # Сортируем и копируем результат обратно в исходный список
        result = self._merge_sort(data.copy())

        # Копируем результат в исходный список
        for i in range(len(data)):
            data[i] = result[i]

        return data

    def _merge_sort(self, arr):
        """Внутренний метод для рекурсивной сортировки"""
        if len(arr) <= 1:
            return arr

        mid = len(arr) // 2
        left = self._merge_sort(arr[:mid])
        right = self._merge_sort(arr[mid:])

        return self._merge(left, right)

    def _merge(self, left, right):
        """Слияние двух отсортированных списков"""
        result = []
        i = j = 0

        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1

        result.extend(left[i:])
        result.extend(right[j:])
        return result
