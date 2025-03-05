import tkinter as tk
from Tkinter.model.debugger.lineDebugger import Debugger
from Tkinter.model.algorithms.algorithmsLine import LineContext
from Tkinter.model.algorithms.algorithmsSecondOrderLine import SecondOrderLineContext
from Tkinter.model.algorithms.algorithmsMenu import LineMenuClass, SecondOrderLineMenuClass
from Tkinter.view.canvas import CanvasView

class GraphicsEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Графический редактор")
        self.root.geometry("800x600")

        # Два контекста: для линий первого и второго порядка
        self.line_context = LineContext()
        self.second_order_context = SecondOrderLineContext()
        self.active_context = None # По умолчанию линии первого порядка

        self.debugger = None

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        self.debug_menu = tk.Menu(self.menu, tearoff=0)
        self.debug_menu.add_command(label="Открыть отладку", command=self.start_debugging)
        self.menu.add_cascade(label="Отладка", menu=self.debug_menu)

        self.toolbar = tk.Frame(self.main_frame, bg="lightgrey", width=200)
        self.toolbar.pack(side=tk.LEFT, fill=tk.Y)

        # Используем CanvasView
        self.canvas_view = CanvasView(self.main_frame)

        self.selected_algorithm = None
        self.click_count = 0
        self.click_points = []

        self.init_toolbar()

    def init_toolbar(self):
        """Создание инструментов панели."""
        tk.Label(self.toolbar, text="Инструменты", bg="lightgrey", font=("Arial", 12, "bold")).pack(pady=10)

        # Отрезки (линии первого порядка)
        line_button = tk.Button(self.toolbar, text="Отрезок")
        line_button.pack(pady=5)
        basic_menu_line = LineMenuClass(self.root, line_button, self.line_context, self.activate_line_tool)
        line_button.config(command=basic_menu_line.show_algorithm_menu)

        # Линии второго порядка (окружность, эллипс и т. д.)
        second_order_button = tk.Button(self.toolbar, text="Линии 2-го порядка")
        second_order_button.pack(pady=5)
        second_order_menu = SecondOrderLineMenuClass(self.root, second_order_button, self.second_order_context, self.activate_second_order_tool)
        second_order_button.config(command=second_order_menu.show_algorithm_menu)

        # Очистка холста
        self.clear_button = tk.Button(self.toolbar, text="Очистить", command=self.clear_area)
        self.clear_button.pack(pady=5)

    def clear_area(self):
        """Очищает Canvas и Debugger (если активен)."""
        self.canvas_view.clear()
        self.click_count = 0
        self.click_points = []
        if self.debugger:
            self.debugger.clear_debug_canvas()

    def activate_line_tool(self):
        """Активирует инструмент рисования отрезков."""
        self.active_context = self.line_context  # Переключаем на контекст линий первого порядка
        self.canvas_view.bind_draw_events(self.start_draw, self.end_draw)
        self.click_count = 0
        self.click_points = []

    def activate_second_order_tool(self):
        """Активирует инструмент рисования линий второго порядка."""
        self.active_context = self.second_order_context  # Переключаем на контекст второго порядка
        self.canvas_view.bind_click_event(self.capture_second_order_points)
        self.click_count = 0
        self.click_points = []

    def start_draw(self, event):
        """Фиксирует начальную точку отрезка."""
        self.canvas_view.start_x, self.canvas_view.start_y = self.canvas_view.get_coordinates(event)

    def end_draw(self, event):
        """Рисует линию и отправляет данные в Debugger."""
        end_x, end_y = self.canvas_view.get_coordinates(event)
        print(f"Рисуем из ({self.canvas_view.start_x}, {self.canvas_view.start_y}) в ({end_x}, {end_y})")

        if self.active_context.get_strategy():
            self.active_context.execute_strategy(
                [self.canvas_view.start_x, self.canvas_view.start_y],
                [end_x, end_y],
                self.canvas_view.canvas
            )
        else:
            print("Ошибка: не выбрана стратегия рисования.")

        if self.debugger:
            self.debugger.set_algorithm(self.selected_algorithm)
            self.debugger.request_manual_input()

    def capture_second_order_points(self, event):
        """Фиксирует точки для линий второго порядка."""
        x, y = self.canvas_view.get_coordinates(event)
        self.click_points.append([x, y])
        self.click_count += 1

        strategy = self.active_context.get_strategy()
        if not strategy:
            print("Ошибка: не выбрана стратегия рисования второго порядка.")
            return

        if strategy.name == "Окружность" and self.click_count == 2:
            # Окружность (2 клика)
            self.draw_second_order_shape(two_points=True)
        elif strategy.name in ["Эллипс", "Гипербола", "Парабола"] and self.click_count == 3:
            # Эллипс, гипербола, парабола (3 клика)
            self.draw_second_order_shape(two_points=False)

    def draw_second_order_shape(self, two_points):
        """Рисует выбранную линию второго порядка."""
        strategy = self.active_context.get_strategy()

        if two_points:
            center, point2 = self.click_points
            self.active_context.execute_strategy(center, point2, None, self.canvas_view.canvas)
        else:
            center, point2, point3 = self.click_points
            self.active_context.execute_strategy(center, point2, point3, self.canvas_view.canvas)

        self.click_count = 0
        self.click_points = []

    def start_debugging(self):
        """Запуск отладчика."""
        if not self.debugger:
            self.debugger = Debugger(self.root)
            self.debugger.debug_window.protocol("WM_DELETE_WINDOW", self.on_debugger_close)

    def on_debugger_close(self):
        """Закрывает окно отладчика и завершает его работу."""
        if self.debugger:
            self.debugger.debug_window.destroy()
            self.debugger = None
