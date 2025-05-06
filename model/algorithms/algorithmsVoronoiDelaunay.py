import numpy as np
from scipy.spatial import Delaunay, Voronoi, voronoi_plot_2d
import tkinter as tk
import math
import itertools # For step counting in Voronoi

# Base Strategy Interface
class VoronoiDelaunayStrategyInterface:
    def compute(self, points):
        raise NotImplementedError
    def draw(self, canvas, points, result, options=None):
        raise NotImplementedError
    def get_name(self):
        raise NotImplementedError

    # --- Methods for Step-by-Step Debugging ---
    def step_compute(self, points):
        """Generator that yields states or the final result for debugging."""
        # Default implementation just computes final result
        result = self.compute(points)
        if result:
            yield result
        else:
            yield None

    def get_total_steps(self, result):
        """Returns the total number of steps needed to visualize the result."""
        raise NotImplementedError

    def draw_step(self, canvas, points, result, step, options=None):
        """Draws the state corresponding to a specific step."""
        raise NotImplementedError
    # -----------------------------------------

# --- Strategies ---

class DelaunayStrategy(VoronoiDelaunayStrategyInterface):
    def compute(self, points):
        """Computes the Delaunay triangulation."""
        if len(points) < 3:
            return None # Need at least 3 points
        try:
            np_points = np.array(points)
            return Delaunay(np_points)
        except Exception as e:
            print(f"Error computing Delaunay: {e}")
            return None

    def draw(self, canvas, points, result, options=None):
        """Draws the full Delaunay triangulation lines."""
        return self._draw_internal(canvas, points, result, step=None, full_draw=True)

    def get_total_steps(self, result):
        """Total steps = number of triangles."""
        return len(result.simplices) if result else 0

    def draw_step(self, canvas, points, result, step, options=None):
        """Draws the Delaunay triangulation up to a certain step (triangle)."""
        return self._draw_internal(canvas, points, result, step=step, full_draw=False, options=options)

    def _draw_internal(self, canvas, points, result, step=None, full_draw=False, options=None):
        """Internal drawing logic for both full and step-by-step.
           Draws cumulatively for step-by-step, highlighting the current step.
        """
        if result is None:
            return []

        # Tag for easy clearing in debugger
        step_tag = options.get("step_tag", "debug_step_element") if options else "debug_step_element"

        drawn_ids = []
        num_simplices_to_draw = len(result.simplices) if full_draw or step is None else step
        simplices_to_draw = itertools.islice(result.simplices, num_simplices_to_draw)

        for i, simplex in enumerate(simplices_to_draw):
            p1_idx, p2_idx, p3_idx = simplex
            x1, y1 = points[p1_idx]
            x2, y2 = points[p2_idx]
            x3, y3 = points[p3_idx]

            is_current_step = not full_draw and (i == step - 1)
            line_width = 3 if is_current_step else 1 # Highlight current step
            line_color = "red" if is_current_step else "blue"

            # Use a specific tag ONLY for step drawing for easier clearing
            current_tags = (step_tag,) if not full_draw else (f"delaunay_line_{i}", "delaunay_element")

            # Draw the triangle edges
            drawn_ids.append(canvas.create_line(x1, y1, x2, y2, fill=line_color, width=line_width, tags=current_tags))
            drawn_ids.append(canvas.create_line(x2, y2, x3, y3, fill=line_color, width=line_width, tags=current_tags))
            drawn_ids.append(canvas.create_line(x3, y3, x1, y1, fill=line_color, width=line_width, tags=current_tags))
        return drawn_ids

    def get_name(self):
        return "Триангуляция Делоне"

class VoronoiStrategy(VoronoiDelaunayStrategyInterface):
    def compute(self, points):
        """Computes the Voronoi diagram."""
        if len(points) < 2:
            return None # Need at least 2 points
        try:
            np_points = np.array(points)
            return Voronoi(np_points)
        except Exception as e:
            print(f"Error computing Voronoi: {e}")
            return None

    def draw(self, canvas, points, result, options=None):
        """Draws the full Voronoi diagram edges."""
        return self._draw_internal(canvas, points, result, step=None, full_draw=True)

    def get_total_steps(self, result):
        """Total steps = number of ridges (edges)."""
        return len(result.ridge_vertices) if result else 0

    def draw_step(self, canvas, points, result, step, options=None):
        """Draws the Voronoi diagram up to a certain step (ridge/edge)."""
        return self._draw_internal(canvas, points, result, step=step, full_draw=False, options=options)

    def _draw_internal(self, canvas, points, result, step=None, full_draw=False, options=None):
        """Internal drawing logic for both full and step-by-step.
           Draws cumulatively for step-by-step, highlighting the current step.
        """
        if result is None:
            return []

        # Tag for easy clearing in debugger
        step_tag = options.get("step_tag", "debug_step_element") if options else "debug_step_element"

        drawn_ids = []
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1: # Avoid issues if canvas not ready
             canvas.update_idletasks()
             canvas_width = canvas.winfo_width()
             canvas_height = canvas.winfo_height()
        center = result.points.mean(axis=0)

        num_ridges_to_draw = len(result.ridge_vertices) if full_draw or step is None else step
        ridge_data = zip(result.ridge_points, result.ridge_vertices)
        ridges_to_draw = itertools.islice(ridge_data, num_ridges_to_draw)

        for i, (pointidx, simplex) in enumerate(ridges_to_draw):
            simplex = np.asarray(simplex)
            # Determine style based on whether it's the current step
            is_current_step = not full_draw and (i == step - 1)
            line_width = 3 if is_current_step else 1

            # Use a specific tag ONLY for step drawing for easier clearing
            current_tags = (step_tag,) if not full_draw else (f"voronoi_line_{i}", "voronoi_element")

            # --- Draw Finite Edges --- 
            if np.all(simplex >= 0):
                v_start = result.vertices[simplex[0]]
                v_end = result.vertices[simplex[1]]
                finite_color = "darkgreen" if is_current_step else "green"
                drawn_ids.append(canvas.create_line(v_start[0], v_start[1], v_end[0], v_end[1], 
                                                    fill=finite_color, width=line_width, tags=current_tags))

            # --- Draw Infinite Edges --- 
            elif np.any(simplex < 0):
                finite_vertex_idx = simplex[simplex >= 0][0]
                t = result.points[pointidx[1]] - result.points[pointidx[0]]
                # Normalize tangent, handle potential zero vector
                norm_t = np.linalg.norm(t)
                if norm_t < 1e-8: continue # Skip if points are coincident
                t /= norm_t
                n = np.array([-t[1], t[0]]) # Normal

                midpoint = result.points[pointidx].mean(axis=0)
                # Calculate direction robustly
                direction = n if np.dot(midpoint - center, n) >= 0 else -n
                # Extend far point
                v_start = result.vertices[finite_vertex_idx]
                far_point = v_start + direction * max(canvas_width, canvas_height) * 1.5 # Adjusted multiplier

                # --- Simple Line Clipping (Intersection with Canvas Box) ---
                # Based on Liang-Barsky or similar principle (simplified)
                clipped_start, clipped_end = self.clip_line(v_start, far_point, 0, 0, canvas_width, canvas_height)

                # Draw the clipped line segment if it's valid
                if clipped_start is not None and clipped_end is not None:
                    infinite_color = "darkorange" if is_current_step else "orange"
                    drawn_ids.append(canvas.create_line(clipped_start[0], clipped_start[1], clipped_end[0], clipped_end[1],
                                                        fill=infinite_color, width=line_width, tags=current_tags))
        return drawn_ids

    def clip_line(self, p1, p2, x_min, y_min, x_max, y_max):
        """Clips a line segment (p1, p2) to a rectangular area.
           Returns (new_p1, new_p2) or (None, None) if fully outside.
           Simplified Cohen-Sutherland or Liang-Barsky idea.
        """
        x1, y1 = p1
        x2, y2 = p2
        dx = x2 - x1
        dy = y2 - y1

        # Check if line is trivially outside (both points on same side)
        # Not fully implemented here for brevity, assume endpoints might be clipped

        t0, t1 = 0.0, 1.0
        checks = [
            (-dx, x1 - x_min), (dx, x_max - x1),
            (-dy, y1 - y_min), (dy, y_max - y1)
        ]

        for p, q in checks:
            if p == 0:
                if q < 0: return None, None # Parallel and outside boundary
            else:
                r = q / p
                if p < 0:
                    if r > t1: return None, None
                    if r > t0: t0 = r
                else:
                    if r < t0: return None, None
                    if r < t1: t1 = r

        # Calculate clipped endpoints
        new_x1 = x1 + t0 * dx
        new_y1 = y1 + t0 * dy
        new_x2 = x1 + t1 * dx
        new_y2 = y1 + t1 * dy

        return (new_x1, new_y1), (new_x2, new_y2)

    def get_name(self):
        return "Диаграмма Вороного"

# --- Context ---

class VoronoiDelaunayContext:
    def __init__(self):
        self.strategy = None # Starts with no selected algorithm

    def set_strategy(self, strategy: VoronoiDelaunayStrategyInterface):
        self.strategy = strategy
        print(f"Strategy set to: {strategy.get_name()}") # Debug print

    def execute_compute(self, points):
        if self.strategy:
            return self.strategy.compute(points)
        else:
            print("Error: No Voronoi/Delaunay strategy selected.")
            return None

    def execute_draw(self, canvas, points, result, options=None):
        if self.strategy:
            return self.strategy.draw(canvas, points, result, options)
        else:
            print("Error: No Voronoi/Delaunay strategy selected for drawing.")
            return []

    # --- Methods for Step-by-Step Debugging ---
    def execute_step_compute(self, points):
        """Executes the step computation via the current strategy."""
        if self.strategy:
            # Since step_compute is a generator, we need to handle it
            # For now, we expect it to yield the final result for visualization purposes
            # If step_compute truly yielded intermediate states, this would need more logic.
            gen = self.strategy.step_compute(points)
            try:
                return next(gen)
            except StopIteration:
                return None
        else:
            print("Error: No Voronoi/Delaunay strategy selected for step compute.")
            return None

    def get_total_steps(self, result):
        """Gets total visualization steps from the current strategy."""
        if self.strategy:
            return self.strategy.get_total_steps(result)
        else:
            print("Error: No Voronoi/Delaunay strategy selected for get_total_steps.")
            return 0

    def execute_draw_step(self, canvas, points, result, step, options=None):
        """Executes the step drawing via the current strategy."""
        if self.strategy:
            return self.strategy.draw_step(canvas, points, result, step, options)
        else:
            print("Error: No Voronoi/Delaunay strategy selected for drawing step.")
            return []
    # -----------------------------------------

    def get_current_strategy_name(self):
        return self.strategy.get_name() if self.strategy else "None"

# --- Menu Class ---

class VoronoiDelaunayMenuClass:
    def __init__(self, root, button, context: VoronoiDelaunayContext, activate_callback):
        self.root = root
        self.button = button
        self.context = context
        self.activate_callback = activate_callback # Called when a strategy is chosen

        self.menu = tk.Menu(self.root, tearoff=0)
        self.algorithms = [
            ("Триангуляция Делоне", DelaunayStrategy()),
            ("Диаграмма Вороного", VoronoiStrategy()),
        ]

        for name, strategy_instance in self.algorithms:
            self.menu.add_command(label=name, command=lambda s=strategy_instance, n=name: self.set_algorithm(s, n))

    def set_algorithm(self, strategy_instance, name):
        self.context.set_strategy(strategy_instance)
        self.button.config(text=f"Ввод: {name}") # Update button text
        if self.activate_callback:
            self.activate_callback() # Activate the corresponding tool in the editor

    def show_algorithm_menu(self):
        # Calculate position near the button
        self.button.update_idletasks() # Ensure button position is up-to-date
        x = self.button.winfo_rootx()
        y = self.button.winfo_rooty() + self.button.winfo_height()
        self.menu.post(x, y) 