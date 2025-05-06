from abc import ABC, abstractmethod

class BaseLineContext(ABC):
    def __init__(self):
        self._strategy = None

    @abstractmethod
    def set_strategy(self, strategy):
        """Устанавливает стратегию."""
        pass

    @abstractmethod
    def get_strategy(self):
        """Возвращает текущую стратегию."""
        pass

    @abstractmethod
    def execute_strategy(self, *args, **kwargs):
        """Выполняет стратегию с переданными аргументами."""
        pass