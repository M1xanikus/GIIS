import tkinter as tk
from tkinter import ttk, messagebox
from model.algorithms.algorithmsLine import DDAStrategy, BresenhamStrategy, WuStrategy
from model.algorithms.algorithmsSecondOrderLine import (
    BresenhamEllipseStrategy, BresenhamCircleStrategy,
    BresenhamParabolaStrategy, BresenhamHyperbolaStrategy
)


class Debugger:
    def __init__(self, root):
        self.step_button = None
        self.debug_window = tk.Toplevel(root)
        self.debug_window.title("Отладка алгоритмов")
        self.debug_window.geometry("900x950")

        self.canvas_size = 500
        self.cell_size = 5

        self.notebook = ttk.Notebook(self.debug_window)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.line_inputs = {}
        self.second_inputs = {}

        self.line_steps = []
        self.second_steps = []
        self.line_step_index = 0
        self.second_step_index = 0

        self.create_line_debugger()
        self.create_second_order_debugger()

    def create_line_debugger(self):
        self.line_frame = tk.Frame(self.notebook)
        self.notebook.add(self.line_frame, text="Линии")

        self.line_canvas = tk.Canvas(self.line_frame, bg="white", width=self.canvas_size, height=self.canvas_size)
        self.line_canvas.pack()
        self.draw_grid(self.line_canvas)

        self.line_algorithm = "ЦДА"

        self.create_controls(self.line_frame, "Линия")

    def create_second_order_debugger(self):
        self.second_order_frame = tk.Frame(self.notebook)
        self.notebook.add(self.second_order_frame, text="Линии 2-го порядка")

        self.second_canvas = tk.Canvas(self.second_order_frame, bg="white", width=self.canvas_size,
                                       height=self.canvas_size)
        self.second_canvas.pack()
        self.draw_grid(self.second_canvas)

        self.second_algorithm = "Окружность"

        self.create_controls(self.second_order_frame, "Второй порядок")

    def create_controls(self, parent, mode):
        frame = tk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame, text="Алгоритм:").grid(row=0, column=0, sticky="w")
        algorithm_menu = ttk.Combobox(frame, values=self.get_algorithm_list(mode))
        algorithm_menu.current(0)
        algorithm_menu.grid(row=0, column=1, padx=5)
        algorithm_menu.bind("<<ComboboxSelected>>", lambda event: self.set_algorithm(event, mode))

        self.create_coordinate_inputs(frame, mode)

        execute_button = tk.Button(frame, text="Выполнить",
                                   command=self.execute_line_algorithm if mode == "Линия" else self.execute_second_order_algorithm)
        execute_button.grid(row=4, column=0, columnspan=2, pady=5)

        step_button = tk.Button(frame, text="Шаг вперед", command=lambda: self.step_forward(mode), state=tk.DISABLED)
        step_button.grid(row=4, column=2, columnspan=2, pady=5)

        if mode == "Линия":
            self.line_algorithm_menu = algorithm_menu
            self.line_step_button = step_button
        else:
            self.second_algorithm_menu = algorithm_menu
            self.second_step_button = step_button

    def get_algorithm_list(self, mode):
        return ["ЦДА", "Брезенхем", "Ву"] if mode == "Линия" else ["Окружность", "Эллипс", "Парабола", "Гипербола"]

    def create_coordinate_inputs(self, frame, mode):
        labels = ["X1", "Y1", "X2", "Y2"] if mode == "Линия" else ["X1", "Y1", "X2", "Y2", "X3", "Y3"]

        # Выбираем нужный словарь
        inputs = self.line_inputs if mode == "Линия" else self.second_inputs

        for i, label in enumerate(labels):
            tk.Label(frame, text=label + ":").grid(row=(i // 2) + 1, column=(i % 2) * 2, sticky="w")
            entry = tk.Entry(frame, width=5)
            entry.grid(row=(i // 2) + 1, column=(i % 2) * 2 + 1, padx=5)
            inputs[label] = entry

        # Если это "Второй порядок", скрываем X3, Y3 по умолчанию
        if mode == "Второй порядок":
            self.third_point_labels = [inputs["X3"].grid_info(), inputs["Y3"].grid_info()]
            inputs["X3"].grid_remove()
            inputs["Y3"].grid_remove()

    def set_algorithm(self, event, mode):
        if mode == "Линия":
            self.line_algorithm = self.line_algorithm_menu.get()
        else:
            self.second_algorithm = self.second_algorithm_menu.get()

            if self.second_algorithm == "Окружность":
                self.second_inputs["X3"].grid_remove()
                self.second_inputs["Y3"].grid_remove()
            else:
                self.second_inputs["X3"].grid(row=self.third_point_labels[0]["row"],
                                              column=self.third_point_labels[0]["column"])
                self.second_inputs["Y3"].grid(row=self.third_point_labels[1]["row"],
                                              column=self.third_point_labels[1]["column"])

    def execute_line_algorithm(self):
        self.clear_canvas("Линия")
        self.line_steps = []
        self.line_step_index = 0

        try:
            x1, y1, x2, y2 = map(int, [self.line_inputs[label].get() for label in ["X1", "Y1", "X2", "Y2"]])
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числовые значения!")
            return

        strategy_class = {"ЦДА": DDAStrategy, "Брезенхем": BresenhamStrategy, "Ву": WuStrategy}.get(self.line_algorithm)
        if strategy_class:
            strategy = strategy_class()
            strategy.execute([x1, y1], [x2, y2], canvas=None, debugger=self)
            if self.line_steps:
                self.line_step_button.config(state=tk.NORMAL)
            else:
                self.line_step_button.config(state=tk.DISABLED)

    def execute_second_order_algorithm(self):
        self.clear_canvas("Второй порядок")
        self.second_steps = []
        self.second_step_index = 0

        try:
            point1 = (int(self.second_inputs["X1"].get()), int(self.second_inputs["Y1"].get()))
            point2 = (int(self.second_inputs["X2"].get()), int(self.second_inputs["Y2"].get()))
            point3 = None
            if self.second_algorithm != "Окружность":
                point3 = (int(self.second_inputs["X3"].get()), int(self.second_inputs["Y3"].get()))
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числовые значения!")
            return

        strategy_class = {
            "Окружность": BresenhamCircleStrategy,
            "Эллипс": BresenhamEllipseStrategy,
            "Парабола": BresenhamParabolaStrategy,
            "Гипербола": BresenhamHyperbolaStrategy
        }.get(self.second_algorithm)

        if strategy_class:
            strategy = strategy_class()
            strategy.execute(point1, point2, point3, canvas=None, debugger=self)
            if self.second_steps:
                self.second_step_button.config(state=tk.NORMAL)
            else:
                self.second_step_button.config(state=tk.DISABLED)

    def draw_grid(self, canvas):
        for x in range(0, self.canvas_size, self.cell_size):
            canvas.create_line(x, 0, x, self.canvas_size, fill="lightgrey")
        for y in range(0, self.canvas_size, self.cell_size):
            canvas.create_line(0, y, self.canvas_size, y, fill="lightgrey")

    def clear_canvas(self, mode):
        canvas = self.line_canvas if mode == "Линия" else self.second_canvas
        canvas.delete("all")
        self.draw_grid(canvas)

    def record_step(self, x, y, intensity=1.0, mode="Линия"):
        if mode == "Линия":
            self.line_steps.append((x, y, intensity))
        elif mode == "Второй порядок":
            self.second_steps.append((x, y, intensity))
        else:
            print(f"[Debugger] Неизвестный режим для записи шага: {mode}")

    def step_forward(self, mode="Линия"):
        if mode == "Линия":
            steps = self.line_steps
            step_index = self.line_step_index
            canvas = self.line_canvas
            button = self.line_step_button
        else: # Второй порядок
            steps = self.second_steps
            step_index = self.second_step_index
            canvas = self.second_canvas
            button = self.second_step_button

        if 0 <= step_index < len(steps):
            x, y, intensity = steps[step_index]
            # Basic check: Map algorithm coordinates to debugger grid coordinates
            # Assuming algorithm coordinates are relative to 0,0
            # And debugger grid cells are 0 to canvas_size/cell_size
            grid_x = x * self.cell_size
            grid_y = y * self.cell_size

            grayscale = int(255 * (1 - intensity))
            color = f"#{grayscale:02x}{grayscale:02x}{grayscale:02x}"

            # Draw on the debugger canvas using grid coordinates
            canvas.create_rectangle(grid_x, grid_y,
                                    grid_x + self.cell_size, grid_y + self.cell_size,
                                    outline=color, fill=color, tags="step") # Add tag

            # Increment index
            if mode == "Линия":
                self.line_step_index += 1
                step_index = self.line_step_index # Update for button check
            else:
                self.second_step_index += 1
                step_index = self.second_step_index # Update for button check

            # Disable button if last step was drawn
            if step_index >= len(steps):
                button.config(state=tk.DISABLED)
        else:
            print("[Debugger] Нет больше шагов для отображения или индекс вне диапазона.")
            button.config(state=tk.DISABLED)