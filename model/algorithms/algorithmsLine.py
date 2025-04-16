from abc import ABC, abstractmethod
from .baseLineContext import BaseLineContext
import time # Add time for unique tags



class LineStrategyInterface(ABC):
    @abstractmethod
    def __init__(self):
        self.name = None
    @abstractmethod
    def execute(self, a, b, canvas):
        pass

    @abstractmethod
    def plot(self, canvas, x, y, color):
        pass

class DDAStrategy(LineStrategyInterface):
    def __init__(self):
        self.name = 'ЦДА'
    def execute(self, a, b, canvas, debugger=None):
        shape_tag = f"line_{time.time_ns()}"
        x1, y1 = a
        x2, y2 = b

        dx = x2 - x1
        dy = y2 - y1
        length = max(abs(dx), abs(dy))
        if length == 0: return shape_tag # Handle zero-length line

        x_inc = dx / length
        y_inc = dy / length

        x = x1 + 0.5 * (1 if dx > 0 else -1 if dx < 0 else 0)
        y = y1 + 0.5 * (1 if dy > 0 else -1 if dy < 0 else 0)

        # Use a helper to plot/record
        self._plot_or_record(canvas, debugger, int(x), int(y), 1.0, shape_tag)
        last_plot_x, last_plot_y = int(x), int(y)

        for _ in range(int(length)):
            x += x_inc
            y += y_inc
            plot_x, plot_y = int(x), int(y)
            if (plot_x, plot_y) != (last_plot_x, last_plot_y):
                 self._plot_or_record(canvas, debugger, plot_x, plot_y, 1.0, shape_tag)
                 last_plot_x, last_plot_y = plot_x, plot_y
        return shape_tag

    def _plot_or_record(self, canvas, debugger, x, y, intensity, tag):
        if debugger:
            debugger.record_step(x, y, intensity, "Линия") # Assuming record_step takes intensity and mode
        elif canvas:
             # Intensity handling for DDA? Defaulting to black
             color = "black"
             canvas.create_rectangle(x, y, x + 1, y + 1, outline=color, fill=color, tags=tag)

    # Keep plot for interface, though execute might not call it directly
    def plot(self, canvas, x, y, color="black"):
        canvas.create_rectangle(int(x), int(y), int(x) + 1, int(y) + 1, outline=color, fill=color)


class BresenhamStrategy(LineStrategyInterface):
    def __init__(self):
        self.name = 'Брезенхем'
    def execute(self, a, b, canvas, debugger=None):
        shape_tag = f"line_{time.time_ns()}"
        x1, y1 = map(int, a)
        x2, y2 = map(int, b)

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1

        # Plot the first point
        self._plot_point(canvas, debugger, x1, y1, "black", shape_tag)

        if dx > dy:
            e = 2 * dy - dx
            while x1 != x2:
                if e >= 0:
                    y1 += sy
                    e -= 2 * dx
                x1 += sx
                e += 2 * dy
                self._plot_point(canvas, debugger, x1, y1, "black", shape_tag)
        else:
            e = 2 * dx - dy
            while y1 != y2:
                if e >= 0:
                    x1 += sx
                    e -= 2 * dy
                y1 += sy
                e += 2 * dx
                self._plot_point(canvas, debugger, x1, y1, "black", shape_tag)

        return shape_tag

    def _plot_point(self, canvas, debugger, x, y, color, tag):
        if debugger:
            debugger.record_step(x, y, 1.0, "Линия") # Assuming intensity 1.0
        elif canvas:
            canvas.create_rectangle(x, y, x + 1, y + 1, outline=color, fill=color, tags=tag)

    # Keep plot for interface
    def plot(self, canvas, x, y, color="black"):
        canvas.create_rectangle(int(x), int(y), int(x) + 1, int(y) + 1, outline=color, fill=color)


class WuStrategy(LineStrategyInterface):
    def __init__(self):
        self.name = 'Ву'
    def plot(self, canvas, x, y, intensity=1.0, color=None):
        """Реализация абстрактного метода plot (игнорируем color, используем intensity)."""
        # This plot method might not be directly called if _plot_wu is used internally,
        # but it needs to exist to satisfy the interface.
        self._plot_wu(canvas, None, int(x), int(y), intensity, tag=None) # Plot single point without tag

    def execute(self, a, b, canvas, debugger=None):
        shape_tag = f"line_{time.time_ns()}"
        x1, y1 = a
        x2, y2 = b

        dx = x2 - x1
        dy = y2 - y1

        # Handle vertical/horizontal/single point cases without main loop
        if dx == 0 and dy == 0:
            self._plot_wu(canvas, debugger, int(x1), int(y1), 1.0, shape_tag)
            return shape_tag
        if dx == 0:
            for y in range(min(int(y1), int(y2)), max(int(y1), int(y2)) + 1):
                 self._plot_wu(canvas, debugger, int(x1), y, 1.0, shape_tag)
            return shape_tag
        if dy == 0:
            for x in range(min(int(x1), int(x2)), max(int(x1), int(x2)) + 1):
                 self._plot_wu(canvas, debugger, x, int(y1), 1.0, shape_tag)
            return shape_tag

        steep = abs(dy) > abs(dx)
        if steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
            dx, dy = dy, dx

        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
            dx = abs(dx) # dx should be positive now
            dy = y2 - y1 # recalculate dy with correct sign

        gradient = dy / dx

        # handle first endpoint
        xend = round(x1)
        yend = y1 + gradient * (xend - x1)
        xgap = 1 - ((x1 + 0.5) % 1) # fractional part from 0.5
        xpxl1 = int(xend)
        ypxl1 = int(yend)
        if steep:
            self._plot_wu(canvas, debugger, ypxl1,     xpxl1, (1 - (yend % 1)) * xgap, shape_tag)
            self._plot_wu(canvas, debugger, ypxl1 + 1, xpxl1,    (yend % 1)  * xgap, shape_tag)
        else:
            self._plot_wu(canvas, debugger, xpxl1, ypxl1,     (1 - (yend % 1)) * xgap, shape_tag)
            self._plot_wu(canvas, debugger, xpxl1, ypxl1 + 1,    (yend % 1)  * xgap, shape_tag)
        intery = yend + gradient # first y-intersection for the main loop

        # handle second endpoint
        xend = round(x2)
        yend = y2 + gradient * (xend - x2)
        xgap = (x2 + 0.5) % 1
        xpxl2 = int(xend)
        ypxl2 = int(yend)
        if steep:
            self._plot_wu(canvas, debugger, ypxl2,     xpxl2, (1 - (yend % 1)) * xgap, shape_tag)
            self._plot_wu(canvas, debugger, ypxl2 + 1, xpxl2,    (yend % 1)  * xgap, shape_tag)
        else:
            self._plot_wu(canvas, debugger, xpxl2, ypxl2,     (1 - (yend % 1)) * xgap, shape_tag)
            self._plot_wu(canvas, debugger, xpxl2, ypxl2 + 1,    (yend % 1)  * xgap, shape_tag)

        # main loop
        if steep:
            for x in range(xpxl1 + 1, xpxl2):
                self._plot_wu(canvas, debugger, int(intery),     x, 1 - (intery % 1), shape_tag)
                self._plot_wu(canvas, debugger, int(intery) + 1, x,    (intery % 1), shape_tag)
                intery += gradient
        else:
            for x in range(xpxl1 + 1, xpxl2):
                self._plot_wu(canvas, debugger, x, int(intery),     1 - (intery % 1), shape_tag)
                self._plot_wu(canvas, debugger, x, int(intery) + 1,    (intery % 1), shape_tag)
                intery += gradient

        return shape_tag

    def _plot_wu(self, canvas, debugger, x, y, intensity, tag):
        if intensity < 0: intensity = 0
        if intensity > 1: intensity = 1
        if debugger:
            debugger.record_step(x, y, intensity, "Линия") # Pass intensity
        elif canvas:
            grayscale = int(255 * (1 - intensity))
            color = f"#{grayscale:02x}{grayscale:02x}{grayscale:02x}"
            canvas.create_rectangle(x, y, x + 1, y + 1, outline=color, fill=color, tags=tag)



class LineContext(BaseLineContext):
    def __init__(self):
        self.__strategy: LineStrategyInterface = None

    def set_strategy(self, strategy: LineStrategyInterface):
        self.__strategy = strategy

    def get_strategy(self):
        return self.__strategy

    def execute_strategy(self, a, b, canvas, debugger=None):
        if self.__strategy:
            # Pass debugger if available, strategy should handle it
            return self.__strategy.execute(a, b, canvas, debugger=debugger)
        return None
