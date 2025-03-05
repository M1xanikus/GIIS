import tkinter as tk

class CanvasView:
    def __init__(self, parent):
        """Инициализирует Canvas и размещает его на экране."""
        self.canvas = tk.Canvas(parent, bg="white")
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.start_x = None
        self.start_y = None

    def get_canvas(self):
        """Возвращает объект canvas."""
        return self.canvas

    def bind_draw_events(self, start_callback, end_callback):
        """Привязывает события для начала и конца рисования (используется для линий первого порядка)."""
        self.canvas.bind("<Button-1>", start_callback)
        self.canvas.bind("<ButtonRelease-1>", end_callback)

    def bind_click_event(self, click_callback):
        """Привязывает событие только для фиксирования точек (используется для линий второго порядка)."""
        self.canvas.bind("<Button-1>", click_callback)

    def clear(self):
        """Очищает Canvas."""
        self.canvas.delete("all")

    def get_coordinates(self, event):
        """Возвращает координаты события."""
        return event.x, event.y
