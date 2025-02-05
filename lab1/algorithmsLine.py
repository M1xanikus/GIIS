from abc import ABC, abstractmethod
import tkinter as tk


class LineStrategyInterface(ABC):
    @abstractmethod
    def execute(self, a,b, canvas):
        pass

    @abstractmethod
    def plot(self, canvas, x, y, color):
        pass

class DDAStrategy(LineStrategyInterface):
    def execute(self, a, b, canvas, debugger=None):
        x1, y1 = a
        x2, y2 = b

        dx = x2 - x1
        dy = y2 - y1
        length = max(abs(dx), abs(dy))

        dx /= length
        dy /= length

        x = x1 + 0.5 * (1 if dx > 0 else -1 if dx < 0 else 0)
        y = y1 + 0.5 * (1 if dy > 0 else -1 if dy < 0 else 0)

        if debugger:
            debugger.record_step(int(x), int(y))

        for _ in range(int(length)):
            x += dx
            y += dy
            if debugger:
                debugger.record_step(int(x), int(y))
            else:
                self.plot(canvas, int(x), int(y))

    def plot(self, canvas, x, y, color="black"):

        size = 1  # Размер точки (1x1 пиксель)
        canvas.create_rectangle(x, y, x + size, y + size, outline=color, fill=color)

class BresenhamStrategy(LineStrategyInterface):
    def execute(self, a, b, canvas, debugger=None):
        x1, y1 = a
        x2, y2 = b

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1

        if dx > dy:
            e = 2 * dy - dx
            while x1 != x2:
                if debugger:
                    debugger.record_step(int(x1), int(y1))
                else:
                    self.plot(canvas, int(x1), int(y1), "black")
                if e >= 0:
                    y1 += sy
                    e -= 2 * dx
                x1 += sx
                e += 2 * dy
        else:
            e = 2 * dx - dy
            while y1 != y2:
                if debugger:
                    debugger.record_step(int(x1), int(y1))
                else:
                    self.plot(canvas, int(x1), int(y1), "black")
                if e >= 0:
                    x1 += sx
                    e -= 2 * dy
                y1 += sy
                e += 2 * dx

        if debugger:
            debugger.record_step(int(x1), int(y1))
        else:
            self.plot(canvas, int(x1), int(y1), "black")


    def plot(self, canvas, x, y, color="black"):
        """Рисует точку на холсте."""
        size = 1  # Размер точки (1x1 пиксель)
        canvas.create_rectangle(x, y, x + size, y + size, outline=color, fill=color)

class WuStrategy(LineStrategyInterface):
    def plot(self, canvas, x, y, intensity):
        """Рисует пиксель с заданной интенсивностью (серый цвет)."""
        grayscale = int(255 * (1 - intensity))  # Инверсия: 1.0 → черный, 0.0 → белый
        color = f"#{grayscale:02x}{grayscale:02x}{grayscale:02x}"
        canvas.create_rectangle(x, y, x + 1, y + 1, outline=color, fill=color)

    def execute(self, a, b, canvas, debugger=None):
        """Алгоритм Ву с отладкой."""
        x1, y1 = a
        x2, y2 = b

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1

        if dx > dy:
            gradient = dy / dx if dx != 0 else 1
            y = y1 + 0.5
            for x in range(x1, x2 + sx, sx):
                y_int = int(y)
                frac = y - y_int  # Дробная часть

                if debugger:
                    debugger.record_step(x, y_int, 1 - frac)
                    debugger.record_step(x, y_int + sy, frac)
                else:
                    self.plot(canvas, x, y_int, 1 - frac)
                    self.plot(canvas, x, y_int + sy, frac)

                y += gradient * sy
        else:
            gradient = dx / dy if dy != 0 else 1
            x = x1 + 0.5
            for y in range(y1, y2 + sy, sy):
                x_int = int(x)
                frac = x - x_int  # Дробная часть

                if debugger:
                    debugger.record_step(x_int, y, 1 - frac)
                    debugger.record_step(x_int + sx, y, frac)
                else:
                    self.plot(canvas, x_int, y, 1 - frac)
                    self.plot(canvas, x_int + sx, y, frac)

                x += gradient * sx

        if debugger:
            debugger.record_step(x2, y2, 1.0)  # Последний пиксель
        else:
            self.plot(canvas, x2, y2, 1.0)

class LineContext:
    def __init__(self):
        self.__strategy:LineStrategyInterface = None

    def set_strategy(self, strategy:LineStrategyInterface):
        self.__strategy = strategy

    def execute_strategy(self, a, b, canvas, debugger=None):
        return self.__strategy.execute(a,b, canvas, debugger )
