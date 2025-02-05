import tkinter as tk
from tkinter import ttk
from algorithmsLine import DDAStrategy, BresenhamStrategy, WuStrategy


class Debugger:
    def __init__(self, root):
        """Создает окно отладки с выбором алгоритма и вводом координат."""
        self.debug_window = tk.Toplevel(root)
        self.debug_window.title("Отладка алгоритма")
        self.debug_window.geometry("850x900")  # Увеличенное окно

        self.canvas_size = 500  # Увеличенный холст
        self.cell_size = 10  # Мелкая сетка
        self.canvas = tk.Canvas(self.debug_window, bg="white", width=self.canvas_size, height=self.canvas_size)
        self.canvas.pack()

        self.draw_grid()

        self.algorithm = "ЦДА"
        self.steps = []  # Список шагов (координат)
        self.step_index = 0  # Текущий шаг
        self.create_controls()

    def draw_grid(self):
        """Рисует увеличенную сетку."""
        for x in range(0, self.canvas_size, self.cell_size):
            self.canvas.create_line(x, 0, x, self.canvas_size, fill="lightgrey")
        for y in range(0, self.canvas_size, self.cell_size):
            self.canvas.create_line(0, y, self.canvas_size, y, fill="lightgrey")

    def create_controls(self):
        """Создает панель управления."""
        self.controls_frame = tk.Frame(self.debug_window)
        self.controls_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(self.controls_frame, text="Алгоритм:").grid(row=0, column=0, sticky="w")
        self.algorithm_menu = ttk.Combobox(self.controls_frame, values=["ЦДА", "Брезенхем", "Ву"])
        self.algorithm_menu.current(0)
        self.algorithm_menu.grid(row=0, column=1, padx=5)
        self.algorithm_menu.bind("<<ComboboxSelected>>", self.set_algorithm)

        tk.Label(self.controls_frame, text="X1:").grid(row=1, column=0, sticky="w")
        self.x1_entry = tk.Entry(self.controls_frame, width=5)
        self.x1_entry.grid(row=1, column=1, padx=5)

        tk.Label(self.controls_frame, text="Y1:").grid(row=1, column=2, sticky="w")
        self.y1_entry = tk.Entry(self.controls_frame, width=5)
        self.y1_entry.grid(row=1, column=3, padx=5)

        tk.Label(self.controls_frame, text="X2:").grid(row=2, column=0, sticky="w")
        self.x2_entry = tk.Entry(self.controls_frame, width=5)
        self.x2_entry.grid(row=2, column=1, padx=5)

        tk.Label(self.controls_frame, text="Y2:").grid(row=2, column=2, sticky="w")
        self.y2_entry = tk.Entry(self.controls_frame, width=5)
        self.y2_entry.grid(row=2, column=3, padx=5)

        self.draw_button = tk.Button(self.controls_frame, text="Построить", command=self.request_manual_input)
        self.draw_button.grid(row=3, column=0, columnspan=2, pady=5)

        self.step_button = tk.Button(self.controls_frame, text="Шаг вперед", command=self.step_forward,
                                     state=tk.DISABLED)
        self.step_button.grid(row=3, column=2, columnspan=2, pady=5)

        self.clear_button = tk.Button(self.controls_frame, text="Сброс", command=self.clear_debug_canvas)
        self.clear_button.grid(row=4, column=0, columnspan=4, pady=5)

    def set_algorithm(self, event=None):
        """Устанавливает выбранный алгоритм."""
        self.algorithm = self.algorithm_menu.get()

    def request_manual_input(self):
        """Считывает координаты и запускает алгоритм."""
        try:
            x1, y1 = int(self.x1_entry.get()), int(self.y1_entry.get())
            x2, y2 = int(self.x2_entry.get()), int(self.y2_entry.get())
        except ValueError:
            print("Ошибка: Введите числовые значения координат!")
            return

        self.execute_algorithm([x1, y1], [x2, y2])

    def execute_algorithm(self, a, b):
        """Запускает алгоритм, но не рисует сразу все пиксели."""
        self.clear_debug_canvas()
        self.steps = []  # Сброс шагов
        self.step_index = 0

        if self.algorithm == "ЦДА":
            DDAStrategy().execute(a, b, self.canvas, self)
        elif self.algorithm == "Брезенхем":
            BresenhamStrategy().execute(a, b, self.canvas, self)
        elif self.algorithm == "Ву":
            WuStrategy().execute(a, b, self.canvas, self)

        self.step_button.config(state=tk.NORMAL)  # Включаем кнопку шагов

    def clear_debug_canvas(self):
        """Очищает холст, сбрасывает шаги и отключает шаговый режим."""
        self.canvas.delete("all")
        self.draw_grid()
        self.steps = []
        self.step_index = 0
        self.step_button.config(state=tk.DISABLED)

    def record_step(self, x, y, intensity=1):
        """Сохраняет пиксель в список шагов с учетом интенсивности (для Ву)."""
        self.steps.append((x, y, intensity))

    def step_forward(self):
        """Отображает один шаг на экране."""
        if self.step_index < len(self.steps):
            x, y, intensity = self.steps[self.step_index]

            grayscale = int(255 * (1 - intensity))  # Интенсивность → градиент серого
            color = f"#{grayscale:02x}{grayscale:02x}{grayscale:02x}"

            self.canvas.create_rectangle(
                x * self.cell_size, y * self.cell_size,
                (x + 1) * self.cell_size, (y + 1) * self.cell_size,
                outline=color, fill=color
            )
            self.step_index += 1  # Следующий шаг

        if self.step_index >= len(self.steps):
            self.step_button.config(state=tk.DISABLED)  # Отключаем кнопку при завершении
