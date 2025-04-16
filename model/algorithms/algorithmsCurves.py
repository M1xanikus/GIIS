import numpy as np
from abc import ABC, abstractmethod
import time # Add time for unique tags

class CurveStrategy(ABC):
    @abstractmethod
    def draw(self, points, canvas):
        pass

class HermiteCurve(CurveStrategy):
    def draw(self, points, canvas):
        if len(points) < 4: return None
        shape_tag = f"curve_{time.time_ns()}" # Unique tag

        M = np.array([
            [2, -2, 1, 1],
            [-3, 3, -2, -1],
            [0, 0, 1, 0],
            [1, 0, 0, 0]
        ])

        last_x, last_y = None, None
        for t in np.arange(0, 1.01, 0.01): # Include endpoint t=1
            T = np.array([t**3, t**2, t, 1])
            x = np.dot(np.dot(T, M), [points[0][0], points[3][0], points[1][0], points[2][0]])
            y = np.dot(np.dot(T, M), [points[0][1], points[3][1], points[1][1], points[2][1]])

            # Draw line segments instead of ovals for a single object ID (or use tags)
            if last_x is not None:
                canvas.create_line(last_x, last_y, x, y, fill='black', tags=(shape_tag, "curve_segment"))
            last_x, last_y = x, y
            # Or keep ovals with tags:
            # canvas.create_oval(x-1, y-1, x+1, y+1, fill='black', outline='black', tags=(shape_tag, "curve_point"))

        return shape_tag # Return the tag

class BezierCurve(CurveStrategy):
    def draw(self, points, canvas):
        if len(points) < 4: return None
        shape_tag = f"curve_{time.time_ns()}" # Unique tag

        M = np.array([
            [-1, 3, -3, 1],
            [3, -6, 3, 0],
            [-3, 3, 0, 0],
            [1, 0, 0, 0]
        ])

        last_x, last_y = None, None
        for t in np.arange(0, 1.01, 0.01): # Include endpoint t=1
            T = np.array([t**3, t**2, t, 1])
            x = np.dot(np.dot(T, M), [p[0] for p in points])
            y = np.dot(np.dot(T, M), [p[1] for p in points])

            if last_x is not None:
                canvas.create_line(last_x, last_y, x, y, fill='black', tags=(shape_tag, "curve_segment"))
            last_x, last_y = x, y
            # Or keep ovals with tags:
            # canvas.create_oval(x-1, y-1, x+1, y+1, fill='black', outline='black', tags=(shape_tag, "curve_point"))

        return shape_tag # Return the tag

class BSplineCurve(CurveStrategy):
    def draw(self, points, canvas):
        if len(points) < 4: return None
        shape_tag = f"curve_{time.time_ns()}" # Unique tag

        M = (1/6) * np.array([
            [-1, 3, -3, 1],
            [3, -6, 3, 0],
            [-3, 0, 3, 0],
            [1, 4, 1, 0]
        ])

        last_x, last_y = None, None
        # Note: B-spline parameter usually goes from 0 to N-3 segments
        # Simplified approach for single segment [0,1]
        for t in np.arange(0, 1.01, 0.01): # Include endpoint t=1
            T = np.array([t**3, t**2, t, 1])
            x = np.dot(np.dot(T, M), [p[0] for p in points])
            y = np.dot(np.dot(T, M), [p[1] for p in points])

            if last_x is not None:
                 canvas.create_line(last_x, last_y, x, y, fill='black', tags=(shape_tag, "curve_segment"))
            last_x, last_y = x, y
            # Or keep ovals with tags:
            # canvas.create_oval(x-1, y-1, x+1, y+1, fill='black', outline='black', tags=(shape_tag, "curve_point"))

        return shape_tag # Return the tag

class CurveContext:
    def __init__(self):
        self._strategy = None
        
    def set_strategy(self, strategy):
        self._strategy = strategy
        
    def get_strategy(self):
        return self._strategy
        
    def execute_strategy(self, points, canvas):
        if self._strategy:
            # Now it returns the tag
            return self._strategy.draw(points, canvas)
        return None
        
    def draw(self, points, canvas):
        if self._strategy:
            self._strategy.draw(points, canvas) 