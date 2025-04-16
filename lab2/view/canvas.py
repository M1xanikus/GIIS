import tkinter as tk
from model.algorithms.algorithmsCurves import CurveContext
from model.algorithms.algorithmsMenu import LineMenuClass, SecondOrderLineMenuClass, CurveMenuClass

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
        """Привязывает события для начала и конца рисования."""
        self.unbind_all() # Ensure clean state
        self.canvas.bind("<Button-1>", start_callback)
        self.canvas.bind("<ButtonRelease-1>", end_callback)

    def bind_click_event(self, click_callback):
        """Привязывает событие только для фиксирования точек."""
        self.unbind_all() # Ensure clean state
        self.canvas.bind("<Button-1>", click_callback)

    def bind_event(self, event_name, callback):
        """Привязывает произвольное событие к холсту."""
        # Note: This doesn't automatically unbind others, careful usage needed
        # or integrate into a more robust binding management system.
        self.canvas.bind(event_name, callback)

    def unbind_all(self):
        """Отвязывает основные события мыши от холста."""
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        # Add any other events that might be bound elsewhere
        # For example, if you use <Enter>, <Leave>, etc.
        # self.canvas.unbind("<Any-Other-Event>")

    def clear(self):
        """Очищает Canvas."""
        self.canvas.delete("all")

    def get_coordinates(self, event):
        """Возвращает координаты события."""
        return event.x, event.y
