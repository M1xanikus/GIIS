import tkinter as tk
from lineDebugger import Debugger
from algorithmsLine import LineContext, WuStrategy, DDAStrategy, BresenhamStrategy


class GraphicsEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Графический редактор")
        self.root.geometry("800x600")
        self.lineContext = LineContext()
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

        self.canvas = tk.Canvas(self.main_frame, bg="white")
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.start_x = None
        self.start_y = None
        self.selected_algorithm = None
        self.algorithm_menu = None

        self.init_toolbar()

    def init_toolbar(self):
        tk.Label(self.toolbar, text="Инструменты", bg="lightgrey", font=("Arial", 12, "bold")).pack(pady=10)
        self.line_button = tk.Button(self.toolbar, text="Отрезок", command=self.show_algorithm_menu)
        self.line_button.pack(pady=5)
        self.clear_button = tk.Button(self.toolbar, text="Очистить", command=self.clear_area)
        self.clear_button.pack(pady=5)

    def clear_area(self):
        self.canvas.delete("all")
        if self.debugger:
            self.debugger.clear_debug_canvas()

    def show_algorithm_menu(self):
        """Показывает список алгоритмов."""
        if self.algorithm_menu:
            self.algorithm_menu.destroy()

        x = self.line_button.winfo_rootx() + self.line_button.winfo_width()
        y = self.line_button.winfo_rooty()

        algorithms = ["ЦДА", "Ву", "Брезенхем"]
        self.algorithm_menu = tk.Toplevel(self.root)
        self.algorithm_menu.geometry(f"150x{25*len(algorithms)}+{x}+{y}")
        self.algorithm_menu.overrideredirect(True)
        self.algorithm_menu.grab_set()

        for algorithm in algorithms:
            btn = tk.Button(self.algorithm_menu, text=algorithm, command=lambda alg=algorithm: self.select_algorithm(alg))
            btn.pack(fill=tk.X)

    def select_algorithm(self, algorithm):
        self.selected_algorithm = algorithm
        print(f"Выбран алгоритм: {self.selected_algorithm}")

        if self.selected_algorithm == "ЦДА":
            self.lineContext.set_strategy(DDAStrategy())
        if self.selected_algorithm == "Брезенхем":
            self.lineContext.set_strategy(BresenhamStrategy())
        if self.selected_algorithm == "Ву":
            self.lineContext.set_strategy(WuStrategy())

        if self.algorithm_menu:
            self.algorithm_menu.destroy()
        self.activate_line_tool()

    def activate_line_tool(self):
        """Активирует инструмент рисования линии."""
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<ButtonRelease-1>", self.end_draw)

    def start_draw(self, event):
        """Фиксирует начальную точку линии."""
        self.start_x, self.start_y = event.x, event.y

    def end_draw(self, event):
        """Рисует линию и отправляет данные в `Debugger`."""
        end_x, end_y = event.x, event.y
        print(f"Рисуем линию из ({self.start_x}, {self.start_y}) в ({end_x}, {end_y}) алгоритмом {self.selected_algorithm}")
        self.lineContext.execute_strategy([self.start_x, self.start_y], [end_x, end_y], self.canvas)

        if self.debugger:
            self.debugger.set_algorithm(self.selected_algorithm)
            self.debugger.request_manual_input()

    def start_debugging(self):
        if not self.debugger:
            self.debugger = Debugger(self.root)
            self.debugger.debug_window.protocol("WM_DELETE_WINDOW", self.on_debugger_close)  # Автоматическое завершение

    def on_debugger_close(self):
        """Закрывает окно отладчика и завершает его работу."""
        if self.debugger:
            self.debugger.debug_window.destroy()
            self.debugger = None


if __name__ == "__main__":
    root = tk.Tk()
    app = GraphicsEditor(root)
    root.mainloop()
