from abc import ABC, abstractmethod
from .baseLineContext import BaseLineContext
from ...view.canvas import CanvasView

class SecondOrderLineStrategyInterface(ABC):
    @abstractmethod
    def __init__(self):
        self.name = None

    @abstractmethod
    def execute(self, center, point2, point3=None, canvas=None, debugger=None):
        pass

    @abstractmethod
    def plot(self, canvas, x, y, color="black"):
        """Отображение точки на холсте."""
        pass


class BresenhamCircleStrategy(SecondOrderLineStrategyInterface):
    def __init__(self):
        self.name = "Окружность"

    def execute(self, center, point2, point3=None, canvas=None, debugger=None):
        """Рисует окружность алгоритмом Брезенхема."""
        cx, cy = center
        px, py = point2
        radius = int(((px - cx) ** 2 + (py - cy) ** 2) ** 0.5)  # Вычисляем радиус

        x, y = 0, radius
        d = 3 - 2 * radius

        while x <= y:
            self.plot_symmetric(canvas, center, x, y, debugger)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def plot_symmetric(self, canvas, center, x, y, debugger=None):
        cx, cy = center
        points = [
            (cx + x, cy + y), (cx - x, cy + y),
            (cx + x, cy - y), (cx - x, cy - y),
            (cx + y, cy + x), (cx - y, cy + x),
            (cx + y, cy - x), (cx - y, cy - x)
        ]

        if debugger:
            for px, py in points:
                debugger.record_step(px, py, 1, "Второй порядок")
        else:
            for px, py in points:
                self.plot(canvas, px, py)

    def plot(self, canvas, x, y, color="black"):
        canvas.create_rectangle(x, y, x + 1, y + 1, outline=color, fill=color)


class BresenhamEllipseStrategy(SecondOrderLineStrategyInterface):
    def __init__(self):
        self.name = "Эллипс"

    def execute(self, center, point2, point3=None, canvas=None, debugger=None):
        """Рисует эллипс алгоритмом Брезенхема."""
        cx, cy = center
        px, py = point2
        qx, qy = point3

        rx = abs(px - cx)  # Полуось X
        ry = abs(qy - cy)  # Полуось Y

        x, y = 0, ry
        rx2, ry2 = rx * rx, ry * ry
        d1 = ry2 - rx2 * ry + 0.25 * rx2

        while ry2 * x < rx2 * y:
            self.plot_symmetric(canvas, cx, cy, x, y, debugger)
            if d1 < 0:
                d1 += 2 * ry2 * (x + 1) + ry2
            else:
                d1 += 2 * ry2 * (x + 1) - 2 * rx2 * (y - 1) + ry2
                y -= 1
            x += 1

        d2 = ry2 * (x + 0.5) ** 2 + rx2 * (y - 1) ** 2 - rx2 * ry2

        while y >= 0:
            self.plot_symmetric(canvas, cx, cy, x, y, debugger)
            if d2 > 0:
                d2 += rx2 * (-2 * y + 3)
            else:
                d2 += 2 * ry2 * (x + 1) + rx2 * (-2 * y + 3)
                x += 1
            y -= 1

    def plot_symmetric(self, canvas, cx, cy, x, y,debugger=None):
        points = [(cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y), (cx - x, cy - y)]
        if debugger:
            for px, py in points:
                debugger.record_step(px, py, 1, "Второй порядок")
        else:
            for px, py in points:
                self.plot(canvas, px, py)

    def plot(self, canvas, x, y, color="black"):
        canvas.create_rectangle(x, y, x + 1, y + 1, outline=color, fill=color)


class BresenhamHyperbolaStrategy(SecondOrderLineStrategyInterface):
    def __init__(self):
        self.name = "Гипербола"

    def execute(self, center, point2, point3=None, canvas=None, debugger=None):
        """Рисует гиперболу алгоритмом Брезенхема."""
        if canvas is None:
            print("Ошибка: canvas не передан в алгоритм гиперболы.")
            return

        cx, cy = center
        px, py = point2
        qx, qy = point3

        a = abs(px - cx)  # Полуось a (по X)
        b = abs(qy - cy)  # Полуось b (по Y)
        dx = a + 10  # Добавляем небольшой сдвиг, чтобы ветви не соединялись

        a2, b2 = a * a, b * b
        x, y = a, 0
        d = b2 * (x * x) - a2 * (y * y) - a2 * b2  # Начальный дискриминант

        # Первая часть (правая и левая ветви)
        while b2 * x * x >= a2 * y * y:
            self.plot_symmetric(canvas, cx, cy, x, y, dx, debugger)
            if d < 0:
                d += 2 * b2 * (y + 1)  # Увеличиваем y
            else:
                d += 2 * b2 * (y + 1) - 2 * a2 * (x - 1)  # Сдвигаем x и y
                x -= 1
            y += 1

        # Вторая часть (верхняя и нижняя ветви)
        d = b2 * (x - 0.5) ** 2 - a2 * (y + 1) ** 2 - a2 * b2
        while x >= 0:
            self.plot_symmetric(canvas, cx, cy, x, y, dx, debugger)
            if d > 0:
                d += -2 * a2 * x  # Уменьшаем x
            else:
                d += 2 * b2 * (y + 1) - 2 * a2 * x  # Увеличиваем y, уменьшаем x
                y += 1
            x -= 1

    def plot_symmetric(self, canvas, cx, cy, x, y, dx, debugger=None):
        """Рисует симметричные точки гиперболы с учетом dx-сдвига."""
        points = [
            (cx - dx + x, cy + y), (cx + dx - x, cy + y),  # Верхние ветви
            (cx - dx + x, cy - y), (cx + dx - x, cy - y)   # Нижние ветви
        ]
        if debugger:
            for px, py in points:
                debugger.record_step(px, py,  1, "Второй порядок")
        else:
            for px, py in points:
                self.plot(canvas, px, py)

    def plot(self, canvas, x, y, color="black"):
        """Рисует пиксель на холсте."""
        canvas.create_rectangle(x, y, x + 1, y + 1, outline=color, fill=color)


class BresenhamParabolaStrategy(SecondOrderLineStrategyInterface):
    def __init__(self):
        self.name = "Парабола"

    def execute(self, center, focus, point3=None, canvas=None, debugger=None):
        """Рисует параболу алгоритмом Брезенхема без артефактов."""
        if canvas is None:
            print("Ошибка: canvas не передан в алгоритм параболы.")
            return

        cx, cy = center
        _, fy = focus  # Y-координата фокуса

        if point3 is None:
            print("Ошибка: третья точка не передана для построения параболы.")
            return
        px, _ = point3  # X-координата для масштабирования

        p = abs(fy - cy)
        if p == 0:
            print("Ошибка: фокус должен быть выше или ниже вершины.")
            return

        direction = 1 if fy > cy else -1
        s = abs(px - cx) / p

        x, y = 0, 0
        d = 1 - 2 * p

        max_y = 1000  # Ограничение высоты

        while y < max_y:
            self.plot_symmetric(canvas, cx, cy, x, y * direction, s,debugger)
            if d < 0:
                d += 2 * y + 3
            else:
                d += 2 * (y - x) + 5
                x += 1
            y = (x ** 2) / (4 * p)  # Плавный переход без скачков

    def plot_symmetric(self, canvas, cx, cy, x, y, s, debugger= None):
        """Рисует точки параболы симметрично."""
        sx = round(s * x)  # Улучшено округление
        points = [
            (cx + sx, cy + round(y)),  # Правая ветвь
            (cx - sx, cy + round(y))  # Левая ветвь
        ]
        if debugger:
            for px, py in points:
                debugger.record_step(px, py,  1, "Второй порядок")
        else:
            for px, py in points:
                self.plot(canvas, px, py)

    def plot(self, canvas, x, y, color="black"):
        """Рисует пиксель на холсте."""
        canvas.create_rectangle(x, y, x + 1, y + 1, outline=color, fill=color)


class SecondOrderLineContext(BaseLineContext):
    def __init__(self):
        self.__strategy: SecondOrderLineStrategyInterface = None

    def set_strategy(self, strategy: SecondOrderLineStrategyInterface):
        self.__strategy = strategy

    def get_strategy(self):
        return self.__strategy

    def execute_strategy(self, center, point2, point3=None, canvas=None, debugger=None):
        if self.__strategy is None:
            raise ValueError("Стратегия не установлена")
        return self.__strategy.execute(center, point2, point3, canvas, debugger)
