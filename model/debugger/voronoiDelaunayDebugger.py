import tkinter as tk
from tkinter import ttk
import numpy as np

class VoronoiDelaunayDebugger:
    POINT_RADIUS = 3
    STEP_TAG = "debug_step_element"
    INITIAL_POINT_TAG = "initial_point"

    def __init__(self, parent_root, context, initial_points):
        self.parent_root = parent_root
        self.context = context
        self.initial_points = initial_points # List of (x, y) tuples
        self.strategy = context.strategy # Get the currently selected strategy
        self.computed_result = None
        self.total_steps = 0
        self.current_step = 0

        if not self.strategy:
            print("DEBUGGER ERROR: No strategy selected in context.")
            return # Cannot proceed without a strategy

        self.debug_window = tk.Toplevel(self.parent_root)
        self.debug_window.title(f"Отладка: {self.strategy.get_name()}")
        self.debug_window.geometry("600x700") # Adjusted size
        self.debug_window.transient(parent_root) # Keep it on top of the main window
        self.debug_window.grab_set() # Make it modal

        # --- Main Frame --- 
        main_frame = ttk.Frame(self.debug_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Canvas --- 
        self.canvas = tk.Canvas(main_frame, bg="white", width=550, height=550)
        self.canvas.pack(pady=10, fill=tk.BOTH, expand=True)

        # --- Controls Frame --- 
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=10)

        self.prev_button = ttk.Button(controls_frame, text="<< Предыдущий шаг", command=self.prev_step, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.step_label = ttk.Label(controls_frame, text="Шаг: 0 / 0", width=15, anchor="center")
        self.step_label.pack(side=tk.LEFT, padx=5, expand=True)

        self.next_button = ttk.Button(controls_frame, text="Следующий шаг >>", command=self.next_step, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=5)

        # --- Initial Setup --- 
        self.run_computation()
        self.draw_initial_state()
        self.update_controls()

        # Handle window close
        self.debug_window.protocol("WM_DELETE_WINDOW", self.on_close)

    def run_computation(self):
        """Runs the computation (gets the final result for step visualization)."""
        print(f"Debugger: Running computation for {self.strategy.get_name()}")
        self.computed_result = self.context.execute_step_compute(self.initial_points)
        if self.computed_result:
            self.total_steps = self.context.get_total_steps(self.computed_result)
            print(f"Debugger: Computation complete. Total visualization steps: {self.total_steps}")
        else:
            print("Debugger: Computation failed or returned no result.")
            self.total_steps = 0

    def draw_initial_state(self):
        """Draws the initial points on the debugger canvas ONLY if they aren't there."""
        if not self.canvas.find_withtag(self.INITIAL_POINT_TAG):
            self.canvas.delete("all") # Clear canvas only if drawing fresh
            r = self.POINT_RADIUS
            for x, y in self.initial_points:
                self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="red", outline="red", tags=(self.INITIAL_POINT_TAG,))

    def show_step(self):
        """Draws the visualization for the current step, clearing only previous step elements."""
        self.draw_initial_state()

        self.canvas.delete(self.STEP_TAG)

        if not self.computed_result or self.current_step <= 0:
            return # Nothing more to draw

        print(f"Debugger: Drawing step {self.current_step} / {self.total_steps}")
        try:
            self.context.execute_draw_step(
                self.canvas,
                self.initial_points,
                self.computed_result,
                self.current_step,
                options={"step_tag": self.STEP_TAG}
            )
        except Exception as e:
            print(f"Error drawing step {self.current_step}: {e}")
            import traceback
            traceback.print_exc()

    def update_controls(self):
        """Updates the step label and button states."""
        self.step_label.config(text=f"Шаг: {self.current_step} / {self.total_steps}")
        self.prev_button.config(state=tk.NORMAL if self.current_step > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_step < self.total_steps else tk.DISABLED)

    def next_step(self):
        """Advances to the next step."""
        if self.current_step < self.total_steps:
            self.current_step += 1
            self.show_step()
            self.update_controls()

    def prev_step(self):
        """Goes back to the previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self.show_step()
            self.update_controls()

    def on_close(self):
        """Handles the closing of the debug window."""
        print("Закрытие окна отладки V/D.")
        self.debug_window.grab_release()
        self.debug_window.destroy() 