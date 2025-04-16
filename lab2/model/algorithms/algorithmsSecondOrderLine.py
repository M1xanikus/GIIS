from abc import ABC, abstractmethod
from .baseLineContext import BaseLineContext
import numpy as np
import time # Add time for unique tags


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
        shape_tag = f"circle_{time.time_ns()}"
        cx, cy = map(int, center)
        px, py = map(int, point2)
        radius = int(((px - cx) ** 2 + (py - cy) ** 2) ** 0.5)

        x, y = 0, radius
        d = 3 - 2 * radius

        while x <= y:
            self._plot_symmetric_circle(canvas, center, x, y, shape_tag, debugger)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1
        return shape_tag

    def _plot_symmetric_circle(self, canvas, center, x, y, tag, debugger=None):
        cx, cy = map(int, center)
        points_to_plot = [
            (cx + x, cy + y), (cx - x, cy + y),
            (cx + x, cy - y), (cx - x, cy - y),
            (cx + y, cy + x), (cx - y, cy + x),
            (cx + y, cy - x), (cx - y, cy - x)
        ]
        self._plot_points(canvas, debugger, points_to_plot, tag)

    def _plot_points(self, canvas, debugger, points, tag, color="black"):
         if debugger:
            for px, py in points:
                debugger.record_step(px, py, 1.0, "Второй порядок")
         elif canvas:
            for px, py in points:
                 canvas.create_rectangle(px, py, px + 1, py + 1, outline=color, fill=color, tags=tag)

    def plot(self, canvas, x, y, color="black"):
        """Реализация абстрактного метода plot."""
        canvas.create_rectangle(int(x), int(y), int(x) + 1, int(y) + 1, outline=color, fill=color)


class BresenhamEllipseStrategy(SecondOrderLineStrategyInterface):
    def __init__(self):
        self.name = "Эллипс"

    def execute(self, center, point2, point3=None, canvas=None, debugger=None):
        shape_tag = f"ellipse_{time.time_ns()}"
        cx, cy = map(int, center)
        px, py = map(int, point2)
        qx, qy = map(int, point3)

        rx = abs(px - cx)
        ry = abs(qy - cy)
        if rx == 0 or ry == 0: return shape_tag # Handle degenerate case

        x, y = 0, ry
        rx2, ry2 = rx * rx, ry * ry
        d1 = ry2 - rx2 * ry + 0.25 * rx2

        # Region 1
        while ry2 * x < rx2 * y:
            self._plot_symmetric_ellipse(canvas, cx, cy, x, y, shape_tag, debugger)
            if d1 < 0:
                d1 += ry2 * (2 * x + 3)
            else:
                d1 += ry2 * (2 * x + 3) + rx2 * (-2 * y + 2)
                y -= 1
            x += 1

        # Region 2
        d2 = ry2 * (x + 0.5)**2 + rx2 * (y - 1)**2 - rx2 * ry2
        while y >= 0:
            self._plot_symmetric_ellipse(canvas, cx, cy, x, y, shape_tag, debugger)
            if d2 > 0:
                d2 += rx2 * (-2 * y + 3)
            else:
                d2 += ry2 * (2 * x + 2) + rx2 * (-2 * y + 3)
                x += 1
            y -= 1
        return shape_tag

    def _plot_symmetric_ellipse(self, canvas, cx, cy, x, y, tag, debugger=None):
        points_to_plot = [(cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y), (cx - x, cy - y)]
        self._plot_points(canvas, debugger, points_to_plot, tag)

    def _plot_points(self, canvas, debugger, points, tag, color="black"):
         if debugger:
            for px, py in points:
                 debugger.record_step(px, py, 1.0, "Второй порядок")
         elif canvas:
            for px, py in points:
                 canvas.create_rectangle(px, py, px + 1, py + 1, outline=color, fill=color, tags=tag)

    def plot(self, canvas, x, y, color="black"):
        """Реализация абстрактного метода plot."""
        canvas.create_rectangle(int(x), int(y), int(x) + 1, int(y) + 1, outline=color, fill=color)


class BresenhamHyperbolaStrategy(SecondOrderLineStrategyInterface):
    def __init__(self):
        self.name = "Гипербола"

    def execute(self, center, point2, point3, canvas=None, debugger=None):
        shape_tag = f"hyperbola_{time.time_ns()}"
        cx, cy = map(int, center)
        px, py = map(int, point2)
        qx, qy = map(int, point3)

        a = abs(px - cx)
        b = abs(qy - cy)
        if a == 0 or b == 0: return shape_tag # Degenerate

        a2, b2 = a * a, b * b
        limit = 2 * cx # Limit drawing range based on center x? Needs adjustment

        # Branch 1: x starting from a, moving right
        x, y = a, 0
        d = 2 * a2 * y + a2 - b2 * (2 * a - 1)
        while y <= limit: # Limiting condition needs review
             self._plot_symmetric_hyperbola(canvas, cx, cy, x, y, shape_tag, debugger)
             if d < 0:
                 d += a2 * (2 * y + 3)
             else:
                 d += a2 * (2 * y + 3) - b2 * (2 * x + 2)
                 x += 1
             y += 1

        # Branch 2: y starting from limit, moving up? (Original logic seems complex, needs review)
        # The standard Bresenham-like hyperbola needs careful state transition.
        # For simplicity here, we only draw one part based on the standard algorithm
        # derivation approach which usually focuses on dy/dx vs dx/dy changes.
        # A full implementation might need separate loops or state.
        print("Warning: Hyperbola drawing might be incomplete or use a simplified algorithm.")

        return shape_tag

    def _plot_symmetric_hyperbola(self, canvas, cx, cy, x, y, tag, debugger=None):
        points_to_plot = [
            (cx + x, cy + y), (cx - x, cy + y),
            (cx + x, cy - y), (cx - x, cy - y)
        ]
        self._plot_points(canvas, debugger, points_to_plot, tag)

    def _plot_points(self, canvas, debugger, points, tag, color="black"):
         if debugger:
            for px, py in points:
                debugger.record_step(px, py, 1.0, "Второй порядок")
         elif canvas:
            for px, py in points:
                 canvas.create_rectangle(px, py, px + 1, py + 1, outline=color, fill=color, tags=tag)

    def plot(self, canvas, x, y, color="black"):
        """Реализация абстрактного метода plot."""
        canvas.create_rectangle(int(x), int(y), int(x) + 1, int(y) + 1, outline=color, fill=color)


class BresenhamParabolaStrategy(SecondOrderLineStrategyInterface):
    def __init__(self):
        self.name = "Парабола"

    def execute(self, center, focus, point3, canvas=None, debugger=None):
        shape_tag = f"parabola_{time.time_ns()}"
        cx, cy = map(int, center)
        fx, fy = map(int, focus)
        px, py = map(int, point3) # Used to determine width/direction?

        p = abs(fy - cy) # Parameter p (distance vertex to focus/directrix)
        if p == 0: return shape_tag # Degenerate

        limit = 2 * p + abs(px-cx) # Heuristic limit
        direction = 1 if fy > cy else -1

        # Bresenham derivation for parabola y^2 = 4ax or x^2 = 4ay
        # Assume x^2 = 4py variation: x^2 = 4*p*(y-cy) + cx -> (x-cx)^2 = 4p(y-cy)
        # Let X = x-cx, Y = y-cy. X^2 = 4pY

        x, y = 0, 0
        d = 1 - 2 * p # Decision parameter for x^2 = 4py

        while y * direction <= limit: # Limiting based on y relative to vertex
            # Transform back: plot (X+cx, Y+cy)
            self._plot_symmetric_parabola(canvas, cx, cy, x, y * direction, shape_tag, debugger)

            if d < 0:
                # Move vertically (change Y) more easily
                d += 2 * y + 3
            else:
                # Move diagonally (change X and Y)
                d += 2 * y + 3 - 4 * p
                x += 1 # Should be x+=1 for X^2=4pY
            y += 1 # Always increment y (or Y)

        print("Warning: Parabola drawing uses simplified algorithm and limit.")
        return shape_tag

    def _plot_symmetric_parabola(self, canvas, cx, cy, x, y, tag, debugger=None):
         # For (x-cx)^2 = 4p(y-cy) -> plots (cx+x, cy+y) and (cx-x, cy+y)
        points_to_plot = [(cx + x, cy + y), (cx - x, cy + y)]
        self._plot_points(canvas, debugger, points_to_plot, tag)

    def _plot_points(self, canvas, debugger, points, tag, color="black"):
         if debugger:
            for px, py in points:
                debugger.record_step(px, py, 1.0, "Второй порядок")
         elif canvas:
            for px, py in points:
                 canvas.create_rectangle(px, py, px + 1, py + 1, outline=color, fill=color, tags=tag)

    def plot(self, canvas, x, y, color="black"):
        """Реализация абстрактного метода plot."""
        canvas.create_rectangle(int(x), int(y), int(x) + 1, int(y) + 1, outline=color, fill=color)


class SecondOrderLineContext(BaseLineContext):
    def __init__(self):
        self.__strategy: SecondOrderLineStrategyInterface = None

    def set_strategy(self, strategy: SecondOrderLineStrategyInterface):
        self.__strategy = strategy

    def get_strategy(self):
        return self.__strategy

    def execute_strategy(self, center, point2, point3=None, canvas=None, debugger=None):
        if self.__strategy:
            return self.__strategy.execute(center, point2, point3, canvas, debugger)
        return None


class CurveStrategyInterface(ABC):
    @abstractmethod
    def draw(self, points, canvas):
        pass

class HermiteCurve(CurveStrategyInterface):
    def draw(self, points, canvas):
        if len(points) < 4:
            return
        
        # Hermite basis matrix
        M = np.array([
            [2, -2, 1, 1],
            [-3, 3, -2, -1],
            [0, 0, 1, 0],
            [1, 0, 0, 0]
        ])
        
        # Generate points along the curve
        for t in np.arange(0, 1, 0.01):
            T = np.array([t**3, t**2, t, 1])
            
            # Calculate x and y coordinates
            x = np.dot(np.dot(T, M), [points[0][0], points[3][0], points[1][0], points[2][0]])
            y = np.dot(np.dot(T, M), [points[0][1], points[3][1], points[1][1], points[2][1]])
            
            canvas.create_oval(x-1, y-1, x+1, y+1, fill='black')

class BezierCurve(CurveStrategyInterface):
    def draw(self, points, canvas):
        if len(points) < 4:
            return
            
        # Bezier basis matrix
        M = np.array([
            [-1, 3, -3, 1],
            [3, -6, 3, 0],
            [-3, 3, 0, 0],
            [1, 0, 0, 0]
        ])
        
        # Generate points along the curve
        for t in np.arange(0, 1, 0.01):
            T = np.array([t**3, t**2, t, 1])
            
            # Calculate x and y coordinates
            x = np.dot(np.dot(T, M), [p[0] for p in points])
            y = np.dot(np.dot(T, M), [p[1] for p in points])
            
            canvas.create_oval(x-1, y-1, x+1, y+1, fill='black')

class BSplineCurve(CurveStrategyInterface):
    def draw(self, points, canvas):
        if len(points) < 4:
            return
            
        # B-spline basis matrix
        M = (1/6) * np.array([
            [-1, 3, -3, 1],
            [3, -6, 3, 0],
            [-3, 0, 3, 0],
            [1, 4, 1, 0]
        ])
        
        # Generate points along the curve
        for t in np.arange(0, 1, 0.01):
            T = np.array([t**3, t**2, t, 1])
            
            # Calculate x and y coordinates
            x = np.dot(np.dot(T, M), [p[0] for p in points])
            y = np.dot(np.dot(T, M), [p[1] for p in points])
            
            canvas.create_oval(x-1, y-1, x+1, y+1, fill='black')

class CurveContext:
    def __init__(self):
        self._strategy = None
        
    def set_strategy(self, strategy):
        self._strategy = strategy
        
    def get_strategy(self):
        return self._strategy
        
    def execute_strategy(self, points, canvas):
        if self._strategy:
            self._strategy.draw(points, canvas)
