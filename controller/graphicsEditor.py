import tkinter as tk
from tkinter import ttk, colorchooser # Добавляем colorchooser
from model.debugger.lineDebugger import Debugger
# --- Импорт отладчика V/D ---
from model.debugger.voronoiDelaunayDebugger import VoronoiDelaunayDebugger
# ---------------------------
from model.algorithms.algorithmsLine import LineContext, LineStrategyInterface
from model.algorithms.algorithmsSecondOrderLine import SecondOrderLineContext, SecondOrderLineStrategyInterface
from model.algorithms.algorithmsCurves import CurveContext, CurveStrategy
from model.algorithms.algorithmsMenu import LineMenuClass, SecondOrderLineMenuClass, CurveMenuClass
from model.algorithms.algorithmsPolygon import PolygonContext, PolygonMenuClass
from view.canvas import CanvasView
from view.opengl_view import run_opengl_view
from view.transform_controls import TransformControls
import math # Import math for distance calculation
import time # Import time for unique handle tags
import multiprocessing # Add multiprocessing
# Import 2D transformations
from model.transformations import translate_2d, rotate_2d, scale_2d, get_center
# --- Импортируем функции анализа ---
import model.polygon_analysis as pa
# ---------------------------------
# --- Импортируем классы заливки ---
from model.algorithms.algorithmsFill import FillContext, FillMenuClass
# --------------------------------
# --- Импорт Вороной/Делоне ---
from model.algorithms.algorithmsVoronoiDelaunay import VoronoiDelaunayContext, VoronoiDelaunayMenuClass
# ----------------------------
# --- Импорт Pillow для заливки ---
try:
    from PIL import Image, ImageDraw, ImageTk
except ImportError:
    print("ОШИБКА: Для работы алгоритмов заливки Flood Fill и Scanline Seed Fill")
    print("        необходима библиотека Pillow. Установите ее: pip install Pillow")
    Image = None
    ImageDraw = None
    ImageTk = None
# --------------------------------

class GraphicsEditor:
    HANDLE_SIZE = 3 # Half-size for drawing handles (e.g., 3x3 pixels around the point)
    SNAP_RADIUS = 5 # Radius for snapping/selecting handles
    DOCKING_RADIUS = 10 # Radius for curve endpoint docking
    TEMP_POINT_RADIUS = 2 # Radius for temporary polygon points
    TEMP_VD_POINT_RADIUS = 3 # Radius for Voronoi/Delaunay input points

    def __init__(self, root):
        self.root = root
        self.root.title("Графический редактор")
        self.root.geometry("800x600")

        # Два контекста: для линий первого и второго порядка
        self.line_context = LineContext()
        self.second_order_context = SecondOrderLineContext()
        self.curve_context = CurveContext()
        self.polygon_context = PolygonContext() # <-- Инициализация контекста полигонов
        self.voronoi_delaunay_context = VoronoiDelaunayContext() # --- Инициализация контекста Вороной/Делоне ---
        self.active_context = None # Текущий активный контекст (рисования или None) # Moved after all contexts are initialized
        self.last_active_draw_context = None # Запоминаем последний инструмент рисования
        self.fill_context = FillContext() # <-- Инициализация контекста заливки
        # -----------------------------------------

        self.debugger = None # For line debugging
        # --- V/D Debugger State ---
        self.vd_debugger = None
        self.vd_debug_mode_active = tk.BooleanVar(value=False)
        # -------------------------
        self.debug_mode_active = tk.BooleanVar(value=False) # General debug flag for transforms

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        # --- Меню Отладка ---
        self.debug_menu = tk.Menu(self.menu, tearoff=0)
        self.debug_menu.add_command(label="Открыть отладку линий", command=self.start_debugging)
        self.debug_menu.add_checkbutton(label="Отладка Трансформаций (Консоль)",
                                       variable=self.debug_mode_active,
                                       command=self.toggle_transform_debug)
        # --- Add V/D Debug Toggle to Menu ---
        self.debug_menu.add_checkbutton(label="Отладка Вороной/Делоне (Пошагово)",
                                       variable=self.vd_debug_mode_active,
                                       command=self.toggle_vd_debug)
        # ------------------------------------
        self.menu.add_cascade(label="Отладка", menu=self.debug_menu)
        # ------------------

        # --- Меню Анализ Полигона ---
        self.analysis_menu = tk.Menu(self.menu, tearoff=0)
        self.analysis_menu.add_command(label="Проверить выпуклость", command=lambda: self.enter_polygon_analysis_mode("check_convex"))
        self.analysis_menu.add_command(label="Показать внутренние нормали", command=lambda: self.enter_polygon_analysis_mode("show_normals"))
        self.analysis_menu.add_command(label="Пересечение с отрезком", command=lambda: self.enter_polygon_analysis_mode("segment_intersection"))
        self.analysis_menu.add_command(label="Принадлежность точки", command=lambda: self.enter_polygon_analysis_mode("point_in_polygon"))
        self.menu.add_cascade(label="Анализ полигона", menu=self.analysis_menu, state=tk.DISABLED) # Изначально неактивно
        # ---------------------------

        self.toolbar = tk.Frame(self.main_frame, bg="lightgrey", width=200)
        self.toolbar.pack(side=tk.LEFT, fill=tk.Y)

        # Используем CanvasView
        self.canvas_view = CanvasView(self.main_frame)

        # State for drawing and editing
        self.click_count = 0
        self.click_points = []
        self.drawn_items = [] # Store info about drawn shapes {id, type, points, handles, strategy}
        self.edit_mode = False
        self.selected_item_index = None # Index in self.drawn_items
        self.selected_handle_index = None # Index of the handle within the item's points/handles
        self.drag_start_pos = None # Store initial position for dragging
        # --- State for Voronoi/Delaunay ---
        self.vd_input_points = [] # Points specifically for V/D calculation
        self.vd_temp_point_ids = [] # Canvas IDs of temporary points shown during input
        self.vd_result_ids = [] # Canvas IDs of the drawn V/D diagram elements
        # ---------------------------------

        # --- Состояние для анализа полигонов ---
        self.analysis_mode = None # None, "check_convex", "show_normals", "select_poly_for_intersect", "draw_intersect_segment", "select_poly_for_point_test", "pick_point_for_test"
        self.selected_polygon_for_analysis_idx = None
        self.analysis_feedback_items = [] # ID временных элементов на холсте (нормали, точки пересечения)
        # -------------------------------------
        # --- Состояние для заливки полигонов ---
        self.fill_mode = None # None, "select_polygon", "pick_seed"
        self.selected_polygon_for_fill_idx = None
        self.fill_color = "blue" # Цвет заливки по умолчанию
        self.current_fill_photo_image = None # Ссылка на PhotoImage для PIL заливок
        # ------------------------------------

        # --- 3D Mode State ---
        self.opengl_process = None
        self.command_queue = None
        self.transform_controls_window = None
        self.mode_3d_button = None # To change its state
        # ---------------------

        # --- 2D Transformation State & Controls ---
        self.transform_2d_frame = None # Frame for 2D controls
        self.translate_x_var = tk.DoubleVar(value=0.0)
        self.translate_y_var = tk.DoubleVar(value=0.0)
        self.rotate_angle_var = tk.DoubleVar(value=0.0)
        self.scale_x_var = tk.DoubleVar(value=1.0)
        self.scale_y_var = tk.DoubleVar(value=1.0)
        # -----------------------------------------

        # Toolbar Buttons
        self.edit_button = None
        self.mode_3d_button = None
        self.build_hull_button = None
        self.build_vd_button = None # Button for Voronoi/Delaunay

        self.init_toolbar()
        # Set default tool (e.g., line tool)
        self.activate_line_tool()

        # Ensure proper cleanup on main window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_main_window_close)

    def init_toolbar(self):
        """Создание инструментов панели, включая кнопку 3D режима."""
        tk.Label(self.toolbar, text="Режимы", bg="lightgrey", font=("Arial", 12, "bold")).pack(pady=5)

        # Кнопка Редактировать
        self.edit_button = tk.Button(self.toolbar, text="Редактировать", command=self.toggle_edit_mode)
        self.edit_button.pack(pady=5, fill=tk.X)

        # --- Кнопка 3D Режим ---
        self.mode_3d_button = tk.Button(self.toolbar, text="3D Режим", command=self.toggle_3d_mode)
        self.mode_3d_button.pack(pady=5, fill=tk.X)
        # -----------------------

        tk.Label(self.toolbar, text="Инструменты 2D", bg="lightgrey", font=("Arial", 12, "bold")).pack(pady=15)

        # Отрезки (линии первого порядка)
        line_button = tk.Button(self.toolbar, text="Отрезок")
        line_button.pack(pady=5, fill=tk.X)
        basic_menu_line = LineMenuClass(self.root, line_button, self.line_context, self.activate_line_tool)
        line_button.config(command=basic_menu_line.show_algorithm_menu)

        # Линии второго порядка (окружность, эллипс и т. д.)
        second_order_button = tk.Button(self.toolbar, text="Линии 2-го порядка")
        second_order_button.pack(pady=5, fill=tk.X)
        second_order_menu = SecondOrderLineMenuClass(self.root, second_order_button, self.second_order_context, self.activate_second_order_tool)
        second_order_button.config(command=second_order_menu.show_algorithm_menu)

        # Кривые (Эрмита, Безье, B-сплайн)
        curve_button = tk.Button(self.toolbar, text="Кривые")
        curve_button.pack(pady=5, fill=tk.X)
        curve_menu = CurveMenuClass(self.root, curve_button, self.curve_context, self.activate_curve_tool)
        curve_button.config(command=curve_menu.show_algorithm_menu)

        # --- Выпуклые оболочки ---
        polygon_button = tk.Button(self.toolbar, text="Выпуклая оболочка")
        polygon_button.pack(pady=5, fill=tk.X)
        polygon_menu = PolygonMenuClass(self.root, polygon_button, self.polygon_context, self.activate_polygon_tool)
        polygon_button.config(command=polygon_menu.show_algorithm_menu)
        # --------------------------

        # --- Voronoi/Delaunay ---
        vd_button = tk.Button(self.toolbar, text="Диагр./Трианг.") # Short name
        vd_button.pack(pady=5, fill=tk.X)
        vd_menu = VoronoiDelaunayMenuClass(self.root, vd_button, self.voronoi_delaunay_context, self.activate_voronoi_delaunay_tool)
        vd_button.config(command=vd_menu.show_algorithm_menu)
        # ------------------------

        # --- Заливка полигонов ---
        fill_button = tk.Button(self.toolbar, text="Заливка полигона")
        fill_button.pack(pady=5, fill=tk.X)
        # Используем activate_fill_tool как callback для меню
        fill_menu = FillMenuClass(self.root, fill_button, self.fill_context, self.activate_fill_tool)
        fill_button.config(command=fill_menu.show_algorithm_menu)
        # ------------------------

        # --- Кнопка "Построить оболочку" (изначально скрыта) ---
        self.build_hull_button = tk.Button(self.toolbar, text="Построить оболочку", command=self.build_convex_hull, state=tk.DISABLED)
        # Не пакуем ее сразу, она будет упакована/распакована в activate_polygon_tool
        # -------------------------------------------------------

        # --- Кнопка "Построить" для Вороной/Делоне (изначально скрыта) ---
        self.build_vd_button = tk.Button(self.toolbar, text="Построить", command=self.build_voronoi_delaunay, state=tk.DISABLED)
        # Не пакуем ее сразу, она будет упакована/распакована в activate_voronoi_delaunay_tool
        # ---------------------------------------------------------

        # --- Placeholder for 2D Transform Controls (initially hidden) ---
        self.transform_2d_frame = ttk.Frame(self.toolbar)
        # Don't pack it yet, pack when an item is selected
        self.create_2d_transform_controls(self.transform_2d_frame)
        # -----------------------------------------------------------

        # Очистка холста (внизу)
        self.clear_button = tk.Button(self.toolbar, text="Очистить 2D", command=self.clear_area)
        self.clear_button.pack(pady=10, side=tk.BOTTOM, fill=tk.X)

        # --- Кнопка выбора цвета заливки ---
        choose_fill_color_button = tk.Button(self.toolbar, text="Цвет заливки", command=self.choose_fill_color)
        choose_fill_color_button.pack(pady=5, fill=tk.X)
        # ----------------------------------

    def create_2d_transform_controls(self, parent_frame):
        """Создает виджеты для управления 2D трансформациями."""
        ttk.Label(parent_frame, text="Преобразования 2D", font=("Arial", 10, "bold")).pack(pady=5)

        # --- Translation --- 
        trans_frame = ttk.Frame(parent_frame)
        trans_frame.pack(fill=tk.X, pady=2)
        ttk.Label(trans_frame, text="DX:").pack(side=tk.LEFT, padx=2)
        ttk.Entry(trans_frame, textvariable=self.translate_x_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(trans_frame, text="DY:").pack(side=tk.LEFT, padx=2)
        ttk.Entry(trans_frame, textvariable=self.translate_y_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Button(trans_frame, text="Переместить", command=self.apply_translate_2d).pack(side=tk.LEFT, padx=5)

        # --- Rotation --- 
        rot_frame = ttk.Frame(parent_frame)
        rot_frame.pack(fill=tk.X, pady=2)
        ttk.Label(rot_frame, text="Угол:").pack(side=tk.LEFT, padx=2)
        ttk.Entry(rot_frame, textvariable=self.rotate_angle_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Button(rot_frame, text="Повернуть", command=self.apply_rotate_2d).pack(side=tk.LEFT, padx=5)

        # --- Scaling --- 
        scale_frame = ttk.Frame(parent_frame)
        scale_frame.pack(fill=tk.X, pady=2)
        ttk.Label(scale_frame, text="SX:").pack(side=tk.LEFT, padx=2)
        ttk.Entry(scale_frame, textvariable=self.scale_x_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(scale_frame, text="SY:").pack(side=tk.LEFT, padx=2)
        ttk.Entry(scale_frame, textvariable=self.scale_y_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Button(scale_frame, text="Масштаб", command=self.apply_scale_2d).pack(side=tk.LEFT, padx=5)

    def show_2d_transform_controls(self):
        """Показывает панель управления 2D трансформациями."""
        if self.transform_2d_frame and not self.transform_2d_frame.winfo_ismapped():
            # Reset values when showing
            self.translate_x_var.set(0.0)
            self.translate_y_var.set(0.0)
            self.rotate_angle_var.set(0.0)
            self.scale_x_var.set(1.0)
            self.scale_y_var.set(1.0)
            # Pack it below the 2D tools label
            self.transform_2d_frame.pack(pady=10, padx=5, fill=tk.X, before=self.clear_button)

    def hide_2d_transform_controls(self):
        """Скрывает панель управления 2D трансформациями."""
        if self.transform_2d_frame and self.transform_2d_frame.winfo_ismapped():
            self.transform_2d_frame.pack_forget()

    def clear_area(self):
        """Очищает область рисования, включая все элементы и состояния."""
        print("Clearing canvas...")
        self.canvas_view.clear()
        self.drawn_items = []
        self.click_points = []
        self.click_count = 0
        self.selected_item_index = None
        self.selected_handle_index = None
        self.hide_2d_transform_controls() # Hide transform controls on clear
        self.cancel_analysis_mode() # Reset analysis state
        self.cancel_fill_mode() # Reset fill state
        # --- Clear Voronoi/Delaunay state ---
        self.clear_vd_input_points()
        self.clear_vd_results()
        self.vd_input_points = []
        # ------------------------------------
        # Reset active context state if needed (e.g., polygon tool)
        if self.active_context == self.polygon_context:
            if self.build_hull_button:
                self.build_hull_button.config(state=tk.DISABLED)
        elif self.active_context == self.voronoi_delaunay_context:
             if self.build_vd_button:
                 self.build_vd_button.config(state=tk.DISABLED)

        # Optionally reactivate the last drawing tool or a default one
        if self.last_active_draw_context:
            if self.last_active_draw_context == self.line_context:
                self.activate_line_tool()
            elif self.last_active_draw_context == self.second_order_context:
                self.activate_second_order_tool()
            elif self.last_active_draw_context == self.curve_context:
                self.activate_curve_tool()
            elif self.last_active_draw_context == self.polygon_context:
                 self.activate_polygon_tool()
            elif self.last_active_draw_context == self.voronoi_delaunay_context:
                 self.activate_voronoi_delaunay_tool()
            # Add other contexts if necessary
        else:
            self.activate_line_tool() # Default fallback

        print("Canvas cleared.")

    def activate_line_tool(self):
        """Активирует инструмент рисования отрезков."""
        self.active_context = self.line_context  # Переключаем на контекст линий первого порядка
        self.canvas_view.bind_draw_events(self.start_draw, self.end_draw)
        self.click_count = 0
        self.click_points = []
        self.last_active_draw_context = self.line_context # Remember this tool
        self.cancel_analysis_mode() # Выходим из режима анализа при выборе инструмента
        # Показать кнопку "Построить оболочку" и включить ее, если есть точки
        if self.build_hull_button:
            self.build_hull_button.pack(pady=5, fill=tk.X, before=self.clear_button) # <-- Новое размещение перед кнопкой очистки
            if len(self.click_points) >= 3:
                self.build_hull_button.config(state=tk.NORMAL)
            else:
                self.build_hull_button.config(state=tk.DISABLED)

    def activate_second_order_tool(self):
        """Активирует инструмент рисования линий второго порядка."""
        self.active_context = self.second_order_context  # Переключаем на контекст второго порядка
        self.canvas_view.bind_click_event(self.capture_second_order_points)
        self.click_count = 0
        self.click_points = []
        self.last_active_draw_context = self.second_order_context # Remember this tool
        self.cancel_analysis_mode() # Выходим из режима анализа при выборе инструмента

    def activate_curve_tool(self):
        """Активирует инструмент рисования кривых."""
        self.active_context = self.curve_context
        self.canvas_view.bind_click_event(self.capture_curve_points)
        self.click_count = 0
        self.click_points = []
        self.last_active_draw_context = self.curve_context # Remember this tool
        self.cancel_analysis_mode() # Выходим из режима анализа при выборе инструмента

    def activate_polygon_tool(self):
        """Активирует инструмент ввода точек для выпуклой оболочки."""
        print("Активация инструмента: Выпуклая оболочка")
        self.activate_draw_tool_common(
            context=self.polygon_context,
            click_handler=self.capture_polygon_point
        )
        # Показать кнопку "Построить оболочку" и включить ее, если есть точки
        if self.build_hull_button:
             self.build_hull_button.pack(pady=5, fill=tk.X, before=self.clear_button) # <-- Новое размещение перед кнопкой очистки
             if len(self.click_points) >= 3:
                 self.build_hull_button.config(state=tk.NORMAL)
             else:
                 self.build_hull_button.config(state=tk.DISABLED)

    def activate_fill_tool(self):
        """Активирует инструмент заливки полигона."""
        # Don't use activate_draw_tool_common directly as fill is stateful
        # self.activate_draw_tool_common(self.fill_context, click_handler=self.handle_fill_click)
        print("Активация инструмента: Заливка")

        # --- Deactivate other modes --- 
        if self.edit_mode:
             self.edit_mode = False
             self.hide_all_handles()
             if self.edit_button:
                default_bg = self.root.cget('bg')
                self.edit_button.config(relief=tk.RAISED, bg=default_bg)
        self.cancel_analysis_mode()
        self.active_context = None # Fill isn't a drawing context
        self.last_active_draw_context = None # Don't remember fill as a drawing tool
        self.hide_2d_transform_controls()
        self.selected_item_index = None
        self.selected_handle_index = None

        # --- Setup Fill Mode --- 
        self.fill_mode = "select_polygon" # Start by selecting a polygon
        self.selected_polygon_for_fill_idx = None

        # --- Bind only the necessary click handler --- 
        self.canvas_view.unbind_all()
        self.canvas_view.bind_event("<Button-1>", self.handle_fill_click)

        print("Fill tool activated. Click a polygon to select it.")
        # --- Hide build buttons --- 
        if self.build_hull_button:
            self.build_hull_button.pack_forget()
        if self.build_vd_button:
            self.build_vd_button.pack_forget()

    def toggle_edit_mode(self):
        """Переключает режим редактирования."""
        if self.edit_mode:
            self.deactivate_edit_tool()
        else:
            self.activate_edit_tool()

    def activate_edit_tool(self):
        """Активирует режим редактирования опорных точек."""
        if self.edit_mode: return
        print("Активация режима Редактирования")
        self.edit_mode = True
        self.active_context = None # No drawing context active
        self.cancel_analysis_mode() # Выходим из режима анализа при входе в редактирование
        self.click_count = 0
        self.click_points = []
        self.selected_item_index = None
        self.selected_handle_index = None
        self.canvas_view.canvas.delete("temp_polygon_point") # Удаляем временные точки

        # Скрываем кнопку "Построить оболочку"
        if self.build_hull_button and self.build_hull_button.winfo_ismapped():
             self.build_hull_button.pack_forget()

        # Update button appearance
        if self.edit_button:
            self.edit_button.config(relief=tk.SUNKEN, bg="lightblue")

        self.canvas_view.unbind_all()
        self.canvas_view.bind_event("<Button-1>", self.on_canvas_press)
        self.canvas_view.bind_event("<B1-Motion>", self.on_canvas_drag)
        self.canvas_view.bind_event("<ButtonRelease-1>", self.on_canvas_release)

        self.show_all_handles()
        self.hide_2d_transform_controls() # Hide controls when entering edit mode initially
        self.selected_item_index = None # Clear selected item

    def deactivate_edit_tool(self):
        """Деактивирует режим редактирования и возвращает предыдущий инструмент."""
        if not self.edit_mode: return
        print("Деактивация режима Редактирования")
        self.edit_mode = False

        # Reset button appearance
        if self.edit_button:
             default_bg = self.root.cget('bg')
             self.edit_button.config(relief=tk.RAISED, bg=default_bg)

        self.hide_all_handles()
        self.selected_item_index = None
        self.selected_handle_index = None

        # Reactivate last drawing tool or default to line tool
        if self.last_active_draw_context == self.second_order_context:
            self.activate_second_order_tool()
        elif self.last_active_draw_context == self.curve_context:
            self.activate_curve_tool()
        elif self.last_active_draw_context == self.polygon_context:
            self.activate_polygon_tool()
        else: # Default or last was line context
            self.activate_line_tool()

        self.hide_2d_transform_controls()
        self.selected_item_index = None

        # Скрываем кнопку "Построить оболочку" (на всякий случай)
        if self.build_hull_button and self.build_hull_button.winfo_ismapped():
             self.build_hull_button.pack_forget()

        self.cancel_analysis_mode() # Выходим из режима анализа при выборе инструмента рисования

    def activate_draw_tool_common(self, context, click_handler=None, draw_handler=None):
        """Общая логика для активации инструментов рисования."""
        tool_name = "Неизвестный инструмент"
        if context == self.line_context: tool_name = "Отрезок"
        elif context == self.second_order_context: tool_name = "Линии 2-го порядка"
        elif context == self.curve_context: tool_name = "Кривые"
        elif context == self.polygon_context: tool_name = "Выпуклая оболочка"
        # --- Skip activation if context is fill --- 
        elif context == self.fill_context: 
            print("[INFO] activate_draw_tool_common called with fill_context, skipping activation.")
            return 
        # --------------------------------------
        print(f"Активация инструмента: {tool_name}")

        if self.edit_mode:
             print("  (Выход из режима Редактирования)")
             self.edit_mode = False
             self.hide_all_handles()
        self.cancel_analysis_mode() # Выходим из режима анализа при выборе инструмента рисования
        self.cancel_fill_mode() # <- Ensure fill mode is cancelled when switching TO a drawing tool

        self.active_context = context
        self.last_active_draw_context = context # Remember this tool
        self.click_count = 0
        # --- Reset click points only for non-polygon tools --- 
        # Keep click points for polygon tool to allow adding more points
        if context != self.polygon_context:
             self.click_points = []
             self.canvas_view.canvas.delete("temp_polygon_point")
        # ----------------------------------------------------
        self.selected_item_index = None
        self.selected_handle_index = None

        # Скрываем кнопки "Построить", если это не инструмент полигонов/V-D
        if context != self.polygon_context and self.build_hull_button and self.build_hull_button.winfo_ismapped():
             self.build_hull_button.pack_forget()
        if context != self.voronoi_delaunay_context and self.build_vd_button and self.build_vd_button.winfo_ismapped():
             self.build_vd_button.pack_forget()

        self.canvas_view.unbind_all()

        if click_handler:
            self.canvas_view.bind_event("<Button-1>", click_handler)
        if draw_handler:
            start_draw, end_draw = draw_handler
            self.canvas_view.bind_event("<Button-1>", start_draw)
            self.canvas_view.bind_event("<ButtonRelease-1>", end_draw)

        self.hide_2d_transform_controls()
        self.selected_item_index = None

    def start_draw(self, event):
        """Фиксирует начальную точку отрезка (для линий И для анализа пересечений)."""
        # Запоминаем координаты, если активен инструмент линии ИЛИ режим рисования отрезка для анализа
        context_ok = self.active_context == self.line_context
        analysis_mode_ok = self.analysis_mode == "draw_intersect_segment"

        if context_ok or analysis_mode_ok:
            self.canvas_view.start_x, self.canvas_view.start_y = self.canvas_view.get_coordinates(event)
            print(f"[DEBUG] start_draw: Mode={self.analysis_mode}, Context={self.active_context}, start_x set to {self.canvas_view.start_x}")

            # --- Если начали рисовать отрезок для анализа, привязываем событие отпускания --- 
            if analysis_mode_ok and self.canvas_view.start_x is not None:
                print("[DEBUG] start_draw: Binding <ButtonRelease-1> to end_analysis_segment_draw")
                self.canvas_view.bind_event("<ButtonRelease-1>", self.end_analysis_segment_draw)
            # ---------------------------------------------------------------------------
            # Если это обычная линия, событие отпускания уже привязано в activate_line_tool
        else:
            # print("start_draw вызван, но не в режиме линии или анализа пересечений.")
            pass

    def end_draw(self, event):
        """Рисует ЛИНИЮ, сохраняет информацию (включая ТЕГ) и ручки."""
        if self.active_context == self.line_context and self.canvas_view.start_x is not None:
            end_x, end_y = self.canvas_view.get_coordinates(event)
            start_point = [self.canvas_view.start_x, self.canvas_view.start_y]
            end_point = [end_x, end_y]
            points = [start_point, end_point]

            strategy = self.active_context.get_strategy()
            if strategy and isinstance(strategy, LineStrategyInterface):
                # print(f"Рисование линии стратегией: {strategy.name}")
                shape_tag = None
                try:
                    shape_tag = strategy.execute(start_point, end_point, self.canvas_view.canvas)
                    if shape_tag:
                        handle_ids = self.draw_handles(points, shape_tag)
                        for handle_id in handle_ids:
                            self.canvas_view.canvas.itemconfig(handle_id, state=tk.HIDDEN)
                        self.drawn_items.append({
                            "tag": shape_tag,
                            "type": "line",
                            "points": points,
                            "handles": handle_ids,
                            "strategy": strategy
                        })
                        self.update_analysis_menu_state() # Обновляем состояние меню анализа
                        # print(f"Сохранен элемент Линия с тегом: {shape_tag}")
                    else:
                        print("Не удалось получить тег от стратегии линии.")
                except Exception as e:
                    print(f"Ошибка выполнения стратегии линии {strategy.name}: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                     # Reset start point
                     self.canvas_view.start_x = None
                     self.canvas_view.start_y = None
            # ... (rest of the error handling) ...
        else:
             pass # Ignore other contexts or missing start point

    def capture_second_order_points(self, event):
        """Фиксирует точки для ЛИНИЙ ВТОРОГО ПОРЯДКА, рисует, сохраняет (с ТЕГОМ)."""
        if self.active_context != self.second_order_context: return

        x, y = self.canvas_view.get_coordinates(event)
        self.click_points.append([x, y])
        self.click_count = len(self.click_points) # Use length of list
        print(f"Захвачена точка {self.click_count} для линии 2-го порядка: ({x}, {y})")

        strategy = self.active_context.get_strategy()
        if not strategy or not isinstance(strategy, SecondOrderLineStrategyInterface):
            print(f"Ошибка: Не выбрана или неверная стратегия для линий 2-го порядка ({strategy})")
            self.click_points = []
            return

        required_points = 2 if strategy.name == "Окружность" else 3
        print(f"Стратегия '{strategy.name}' требует {required_points} точки. Есть {self.click_count}.")

        if self.click_count == required_points:
            points_to_draw = list(self.click_points)
            # print(f"Рисование {strategy.name} точками: {points_to_draw}")
            shape_tag = None
            try:
                if strategy.name == "Окружность":
                    shape_tag = strategy.execute(points_to_draw[0], points_to_draw[1], None, self.canvas_view.canvas)
                else:
                    shape_tag = strategy.execute(points_to_draw[0], points_to_draw[1], points_to_draw[2], self.canvas_view.canvas)

                if shape_tag:
                    handle_ids = self.draw_handles(points_to_draw, shape_tag)
                    for handle_id in handle_ids:
                        self.canvas_view.canvas.itemconfig(handle_id, state=tk.HIDDEN)
                    self.drawn_items.append({
                        "tag": shape_tag,
                        "type": "second_order",
                        "points": points_to_draw,
                        "handles": handle_ids,
                        "strategy": strategy
                    })
                    self.update_analysis_menu_state()
                    # print(f"Сохранен элемент {strategy.name} с тегом: {shape_tag}")
                else:
                    print(f"Не удалось получить тег от стратегии {strategy.name}.")
            except Exception as e:
                print(f"Ошибка выполнения стратегии {strategy.name}: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # Reset after drawing attempt
                self.click_count = 0
                self.click_points = []

    def capture_curve_points(self, event):
        """Фиксирует точки для КРИВЫХ, рисует, сохраняет (с ТЕГОМ)."""
        if self.active_context != self.curve_context: return

        x, y = self.canvas_view.get_coordinates(event)
        self.click_points.append([x, y])
        self.click_count = len(self.click_points)
        print(f"Захвачена точка {self.click_count} для кривой: ({x}, {y})")

        strategy = self.active_context.get_strategy()
        if not strategy or not isinstance(strategy, CurveStrategy):
            print(f"Ошибка: Не выбрана или неверная стратегия для кривых ({strategy})")
            self.click_points = []
            return

        required_points = 4 # Assuming all curve strategies need 4 points
        print(f"Стратегия кривой требует {required_points} точки. Есть {self.click_count}.")

        if self.click_count == required_points:
            points_to_draw = list(self.click_points)
            # print(f"Рисование кривой точками: {points_to_draw}")
            shape_tag = None
            try:
                shape_tag = strategy.draw(points_to_draw, self.canvas_view.canvas)
                if shape_tag:
                    handle_ids = self.draw_handles(points_to_draw, shape_tag)
                    for handle_id in handle_ids:
                        self.canvas_view.canvas.itemconfig(handle_id, state=tk.HIDDEN)
                    self.drawn_items.append({
                        "tag": shape_tag,
                        "type": "curve",
                        "points": points_to_draw,
                        "handles": handle_ids,
                        "strategy": strategy
                    })
                    self.update_analysis_menu_state()
                    # print(f"Сохранен элемент Кривая с тегом: {shape_tag}")
                else:
                    print(f"Не удалось получить тег от стратегии кривой.")
            except Exception as e:
                print(f"Ошибка выполнения стратегии кривой: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # Reset after drawing attempt
                self.click_count = 0
                self.click_points = []

    def capture_polygon_point(self, event):
        """Фиксирует точки для построения выпуклой оболочки."""
        if self.active_context != self.polygon_context: return

        x, y = self.canvas_view.get_coordinates(event)
        self.click_points.append([x, y])
        print(f"Добавлена точка {len(self.click_points)} для оболочки: ({x}, {y})")

        # Рисуем временную точку на холсте
        r = self.TEMP_POINT_RADIUS
        self.canvas_view.canvas.create_oval(x-r, y-r, x+r, y+r, fill="purple", outline="purple", tags="temp_polygon_point")

        # Включаем кнопку "Построить", если точек достаточно
        if len(self.click_points) >= 3 and self.build_hull_button:
            self.build_hull_button.config(state=tk.NORMAL)

    def build_convex_hull(self):
        """Строит выпуклую оболочку по собранным точкам."""
        if self.active_context != self.polygon_context or len(self.click_points) < 3:
            print("Недостаточно точек для построения оболочки (нужно >= 3).")
            return

        strategy = self.polygon_context.get_strategy()
        if not strategy:
            print("Ошибка: Не выбрана стратегия построения оболочки.")
            return

        points_to_build = list(self.click_points) # Копируем точки
        print(f"Построение оболочки '{strategy.name}' для {len(points_to_build)} точек.")

        shape_tag = None
        hull_points = []
        try:
            shape_tag, hull_points = self.polygon_context.execute_strategy(points_to_build, self.canvas_view.canvas)
            if shape_tag and hull_points:
                # Сохраняем информацию об оболочке. Ручки НЕ создаем для оболочек.
                self.drawn_items.append({
                    "tag": shape_tag,
                    "type": "polygon",
                    "points": hull_points, # Сохраняем ТОЛЬКО точки оболочки
                    "strategy": strategy,
                    "original_points": points_to_build # Сохраняем исходные точки (опционально)
                })
                print(f"Сохранен элемент Выпуклая Оболочка ({strategy.name}) с тегом: {shape_tag}")
                self.update_analysis_menu_state() # Обновляем меню анализа
            else:
                print(f"Не удалось построить оболочку {strategy.name}.")
        except Exception as e:
            print(f"Ошибка выполнения стратегии оболочки {strategy.name}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Очищаем временные точки и сбрасываем состояние
            self.canvas_view.canvas.delete("temp_polygon_point")
            self.click_points = []
            if self.build_hull_button:
                 self.build_hull_button.config(state=tk.DISABLED)
            # Остаемся в режиме полигонов для ввода следующего набора точек

    def start_debugging(self):
        """Запуск отладчика ЛИНИЙ."""
        if not self.debugger:
            print("Запуск отладчика Линий")
            # from model.debugger.lineDebugger import Debugger # Already imported at top
            self.debugger = Debugger(self.root)
            self.debugger.debug_window.protocol("WM_DELETE_WINDOW", self.on_debugger_close)
        else:
            print("Отладчик Линий уже запущен.")

    def on_debugger_close(self):
        """Закрывает окно отладчика ЛИНИЙ."""
        if self.debugger:
            print("Закрытие отладчика Линий")
            self.debugger.debug_window.destroy()
            self.debugger = None

    def toggle_transform_debug(self):
        """Включает/выключает режим отладки трансформаций (вывод в консоль)."""
        if self.debug_mode_active.get():
            print("[Отладка Трансформаций ВКЛЮЧЕНА (вывод в консоль)]")
        else:
            print("[Отладка Трансформаций ВЫКЛЮЧЕНА]")

    def draw_handles(self, points, item_identifier):
        """Рисует 'ручки' для опорных точек, ТЕГИРУЯ их основным тегом элемента."""
        # --- НЕ рисуем ручки для полигонов ---
        # if self.active_context == self.polygon_context:
        #      return [] # Не создаем ручки для оболочек
        # Проверка может быть не надежна, лучше проверять тип элемента при сохранении
        # Сейчас проверка идет перед вызовом этой функции (см. build_convex_hull)
        # -----------------------------------

        handle_ids = []
        main_tag = str(item_identifier) if item_identifier else f"item_orphan_{time.time_ns()}"

        for i, p in enumerate(points):
            x, y = p
            handle_specific_tag = f"handle_{main_tag}_{i}"
            handle_id = self.canvas_view.canvas.create_rectangle(
                x - self.HANDLE_SIZE, y - self.HANDLE_SIZE,
                x + self.HANDLE_SIZE, y + self.HANDLE_SIZE,
                fill="white", outline="black",
                tags=(main_tag, "handle", handle_specific_tag)
            )
            handle_ids.append(handle_id)
        return handle_ids

    def show_all_handles(self):
        """Показывает ручки для всех редактируемых элементов."""
        self.canvas_view.canvas.itemconfig("handle", state=tk.NORMAL)

    def hide_all_handles(self):
        """Скрывает все ручки."""
        self.canvas_view.canvas.itemconfig("handle", state=tk.HIDDEN)

    # --- Event Handlers for Edit Mode ---

    def on_canvas_press(self, event):
        """Обработчик нажатия мыши в режиме редактирования: выбор ручки или элемента."""
        if not self.edit_mode: return

        x, y = event.x, event.y
        # Если активен режим анализа, обрабатываем клик для него
        if self.analysis_mode:
            self.handle_analysis_click(event)
            return

        # Deselect previous item and handle
        if self.selected_item_index is not None and self.selected_handle_index is None:
             # print(f"Deselecting item {self.selected_item_index}")
             self.hide_2d_transform_controls()
        if self.selected_handle_index is not None:
             self.reset_handle_appearance(self.selected_item_index, self.selected_handle_index)

        self.selected_item_index = None
        self.selected_handle_index = None
        self.drag_start_pos = None

        # 1. Check for handle selection (priority)
        closest_handle_info = None
        min_dist_sq = self.SNAP_RADIUS**2

        for item_idx, item in enumerate(self.drawn_items):
            # --- Исключаем полигоны из редактирования ручек ---
            if item.get("type") == "polygon": continue
            # -----------------------------------------------
            if "handles" in item and "points" in item:
                for handle_idx, point in enumerate(item["points"]):
                    px, py = point
                    dist_sq = (x - px)**2 + (y - py)**2
                    if dist_sq <= min_dist_sq:
                        min_dist_sq = dist_sq
                        closest_handle_info = (item_idx, handle_idx)
                # if closest_handle_info and min_dist_sq == 0: break

        if closest_handle_info:
            self.selected_item_index, self.selected_handle_index = closest_handle_info
            self.drag_start_pos = (x, y)
            # print(f"Выбрана ручка {self.selected_handle_index} элемента {self.selected_item_index}")
            handle_id = self.drawn_items[self.selected_item_index]["handles"][self.selected_handle_index]
            self.canvas_view.canvas.itemconfig(handle_id, fill="lightblue")
            self.hide_2d_transform_controls()
            return # Handle selected

        # 2. If no handle selected, check for item selection (including polygons for transforms)
        min_dist_to_item_sq = self.SNAP_RADIUS**2
        selected_item_idx = None
        # Find the closest item overall by checking distance to its points
        for item_idx, item in enumerate(self.drawn_items):
            # --- Полигоны можно выбирать для трансформаций ---
            points_to_check = item.get("points")
            if not points_to_check: continue

            # Check distance to each point of the item
            for p in points_to_check:
                dist_sq = (x - p[0])**2 + (y - p[1])**2
                if dist_sq <= min_dist_to_item_sq:
                    selected_item_idx = item_idx
                    min_dist_to_item_sq = dist_sq
                    break # Found a close point for this item

        if selected_item_idx is not None:
            self.selected_item_index = selected_item_idx
            self.selected_handle_index = None
            print(f"Выбран элемент {self.selected_item_index} (тип: {self.drawn_items[selected_item_idx].get('type')}) для преобразования")
            # --- НЕ показываем ручки для полигонов, даже если выбраны ---
            if self.drawn_items[selected_item_idx].get("type") != "polygon":
                self.show_all_handles() # Show handles for other types
            else:
                self.hide_all_handles() # Hide if polygon is selected
            # --------------------------------------------------------
            self.show_2d_transform_controls() # Show transform controls for ALL selected items
        else:
             # print("Не выбрана ни ручка, ни элемент.")
             self.hide_2d_transform_controls()
             self.hide_all_handles() # Hide handles if nothing is selected

    def on_canvas_drag(self, event):
        """Обработчик перетаскивания: перемещение ТОЛЬКО ручки, обновление данных."""
        if not self.edit_mode or self.selected_item_index is None or self.selected_handle_index is None:
            return # Only drag handles, not whole items here

        nx, ny = event.x, event.y
        item = self.drawn_items[self.selected_item_index]

        # --- Убедимся, что это не полигон (на всякий случай) ---
        if item.get("type") == "polygon": return
        # ---------------------------------------------------

        item["points"][self.selected_handle_index] = [nx, ny]
        handle_id = item["handles"][self.selected_handle_index]
        self.canvas_view.canvas.coords(handle_id,
                                       nx - self.HANDLE_SIZE, ny - self.HANDLE_SIZE,
                                       nx + self.HANDLE_SIZE, ny + self.HANDLE_SIZE)

    def on_canvas_release(self, event):
        """Обработчик отпускания кнопки мыши: проверка стыковки, перерисовка."""
        if not self.edit_mode or self.selected_item_index is None:
             return # Need an item selected

        # If only an item was selected (for transform), do nothing on release
        if self.selected_handle_index is None:
            # print("Item selected, no handle action on release.")
            return

        # --- Handle was dragged and released ---
        current_item_idx = self.selected_item_index
        current_handle_idx = self.selected_handle_index
        item = self.drawn_items[current_item_idx]

        # --- Docking Logic (Only for Curves) ---
        docked = False
        if item.get("type") == "curve" and current_handle_idx in [0, 3]:
            # ... (docking logic remains the same) ...
            current_point = item["points"][current_handle_idx]
            nx, ny = current_point
            # print(f"--- Проверка стыковки для Элемента {current_item_idx}, Ручки {current_handle_idx}...")
            closest_target_info = None
            min_dist_sq = self.DOCKING_RADIUS**2
            for target_item_idx, target_item in enumerate(self.drawn_items):
                if target_item_idx == current_item_idx: continue
                if target_item.get("type") == "curve" and len(target_item.get("points", [])) == 4:
                    target_p0 = target_item["points"][0]
                    dist_sq_p0 = (nx - target_p0[0])**2 + (ny - target_p0[1])**2
                    if dist_sq_p0 < min_dist_sq:
                        min_dist_sq = dist_sq_p0
                        closest_target_info = {"item_idx": target_item_idx, "handle_idx": 0, "coords": target_p0}
                    target_p3 = target_item["points"][3]
                    dist_sq_p3 = (nx - target_p3[0])**2 + (ny - target_p3[1])**2
                    if dist_sq_p3 < min_dist_sq:
                        min_dist_sq = dist_sq_p3
                        closest_target_info = {"item_idx": target_item_idx, "handle_idx": 3, "coords": target_p3}
            if closest_target_info:
                target_coords = closest_target_info["coords"]
                # print(f"---> СТЫКОВКА ручки {current_handle_idx} к ручке {closest_target_info['handle_idx']} элемента {closest_target_info['item_idx']}")
                item["points"][current_handle_idx] = list(target_coords)
                docked = True
            # else: print("--- Подходящая точка для стыковки не найдена ---")
        # --- End Docking Logic ---

        # Redraw the item whose handle was just released
        # print(f"Отпущена ручка {current_handle_idx} элемента {current_item_idx}. Перерисовка.")
        self.redraw_item(current_item_idx) # Redraw handles as well

        # Reset visual feedback for selected handle (after redraw)
        self.reset_handle_appearance(current_item_idx, current_handle_idx)

        # Reset selection state
        self.selected_item_index = None
        self.selected_handle_index = None
        self.drag_start_pos = None

    def reset_handle_appearance(self, item_idx, handle_idx):
        """Вспомогательная функция для сброса внешнего вида ручки."""
        if item_idx < len(self.drawn_items):
            item = self.drawn_items[item_idx]
            # --- Не сбрасываем вид для полигонов (у них нет ручек) ---
            if item.get("type") == "polygon": return
            # -------------------------------------------------------
            if "handles" in item and handle_idx < len(item["handles"]):
                try:
                    handle_id = item["handles"][handle_idx]
                    self.canvas_view.canvas.itemconfig(handle_id, fill="white")
                except tk.TclError: pass
                except IndexError: pass

    def redraw_item(self, item_index):
        """Перерисовывает элемент (включая полигоны), удаляя старый объект и ручки по ТЕГУ."""
        if item_index < 0 or item_index >= len(self.drawn_items): return
        item = self.drawn_items[item_index]
        canvas = self.canvas_view.canvas
        old_tag = item.get("tag")

        # --- 1. Delete old graphics (shape AND handles if they exist) using TAG ---
        if old_tag:
            # print(f"Удаление элементов с тегом: {old_tag}")
            canvas.delete(old_tag)
            item["handles"] = [] # Reset handle list even if none were expected
        else:
             print(f"Предупреждение: Тег не найден для элемента {item_index}.")

        # --- 2. Get strategy, points ---
        strategy = item.get("strategy")
        points = item.get("points") # For polygons, these are the HULL points
        item_type = item.get("type")
        if not strategy or not points: return

        # --- 3. Execute strategy to redraw and GET NEW TAG ---
        new_tag = None
        new_hull_points = None # For polygon redraw
        try:
            if item_type == "line":
                 if len(points) == 2: new_tag = strategy.execute(points[0], points[1], canvas)
            elif item_type == "second_order":
                 if strategy.name == "Окружность" and len(points) == 2: new_tag = strategy.execute(points[0], points[1], None, canvas)
                 elif strategy.name != "Окружность" and len(points) == 3: new_tag = strategy.execute(points[0], points[1], points[2], canvas)
            elif item_type == "curve":
                 if len(points) == 4: new_tag = strategy.draw(points, canvas)
            elif item_type == "polygon":
                 # Re-execute the hull algorithm using the *original* points if stored,
                 # otherwise, just redraw the polygon with the existing hull points.
                 # For transformations, we just need to redraw the hull polygon shape.
                 # The execute strategy expects the *original* points.
                 # For redraw after transform, 'points' contains the *transformed* hull points.
                 # We simply draw a polygon with these points.
                 if points:
                     # Create a unique tag for the potentially transformed polygon
                     base_name = "hull_polygon"
                     if hasattr(strategy, 'name'): base_name = f"hull_{strategy.name.lower()}"
                     new_tag = f"{base_name}_{time.time_ns()}"
                     flat_hull = [coord for pt in points for coord in pt]
                     # Use the outline color defined in the strategy execution if possible
                     # Defaulting to blue for Graham, red for Jarvis if needed
                     outline_color = 'purple' # Default redraw color
                     if strategy.name == "Грэхем": outline_color = 'blue'
                     elif strategy.name == "Джарвис": outline_color = 'red'
                     canvas.create_polygon(flat_hull, outline=outline_color, fill='', width=2, tags=(new_tag, "hull"))
                     # Note: We are NOT re-running the algorithm here, just redrawing the shape
                     # The 'points' in the item dictionary are updated by the transformation method.
                     new_hull_points = points # Hull points remain the same, just transformed
                 else: print("Warning: Cannot redraw polygon, missing points.")
            else: print(f"Error: Unknown item type for redraw: {item_type}")

            item["tag"] = new_tag
            if item_type == "polygon" and new_hull_points:
                item["points"] = new_hull_points # Ensure hull points are up-to-date
            # print(f"Перерисован элемент {item_index}, новый тег: {new_tag}")

        except Exception as e:
            print(f"Ошибка перерисовки элемента {item_index} типа {item_type}: {e}")
            import traceback
            traceback.print_exc()
            item["tag"] = None

        # --- 4. Redraw handles (ONLY for non-polygon types) ---
        if item_type != "polygon":
            new_handle_ids = self.draw_handles(points, new_tag if new_tag else f"item_{item_index}_orphan")
            item["handles"] = new_handle_ids
            # Set handle visibility based on edit mode
            handle_state = tk.NORMAL if self.edit_mode else tk.HIDDEN
            for handle_id in new_handle_ids:
                 try: canvas.itemconfig(handle_id, state=handle_state)
                 except tk.TclError: pass
        else:
            item["handles"] = [] # Ensure polygons have no handles listed

    # --- 3D Mode Methods ---
    def toggle_3d_mode(self):
        """Включает или выключает 3D режим."""
        if self.opengl_process and self.opengl_process.is_alive():
            self.stop_3d_mode()
        else:
            self.start_3d_mode()

    def start_3d_mode(self):
        """Запускает процесс OpenGL и окно управления."""
        if self.opengl_process and self.opengl_process.is_alive():
            print("3D режим уже запущен.")
            return
        print("Запуск 3D режима...")
        self.command_queue = multiprocessing.Queue()
        try:
            self.opengl_process = multiprocessing.Process(target=run_opengl_view, args=(self.command_queue,))
            self.opengl_process.start()
        except Exception as e:
            print(f"Ошибка запуска процесса OpenGL: {e}")
            self.command_queue = None
            return
        if self.transform_controls_window and self.transform_controls_window.winfo_exists():
             self.transform_controls_window.destroy()
        self.transform_controls_window = TransformControls(self.root, self.command_queue)
        self.transform_controls_window.protocol("WM_DELETE_WINDOW", self.on_3d_controls_close)
        if self.mode_3d_button:
            self.mode_3d_button.config(relief=tk.SUNKEN, text="Выйти из 3D", bg="lightgreen")

    def stop_3d_mode(self):
        """Останавливает процесс OpenGL и закрывает окно управления."""
        print("Остановка 3D режима...")
        if self.command_queue:
            try: self.command_queue.put({"type": "quit"})
            except Exception as e: print(f"Ошибка отправки команды выхода: {e}")
        if self.transform_controls_window and self.transform_controls_window.winfo_exists():
            self.transform_controls_window.protocol("WM_DELETE_WINDOW", lambda: None)
            self.transform_controls_window.destroy()
            self.transform_controls_window = None
        if self.opengl_process and self.opengl_process.is_alive():
            self.opengl_process.join(timeout=1.0)
            if self.opengl_process.is_alive():
                self.opengl_process.terminate()
        self.opengl_process = None
        self.command_queue = None
        if self.mode_3d_button:
             default_bg = self.root.cget('bg')
             self.mode_3d_button.config(relief=tk.RAISED, text="3D Режим", bg=default_bg)
        self.activate_line_tool() # Or reactivate last used tool

    def on_3d_controls_close(self):
        """Callback when the TransformControls window is closed by the user."""
        print("Окно управления 3D закрыто пользователем.")
        self.stop_3d_mode()

    def on_main_window_close(self):
        """Handles closing the main Tkinter window."""
        print("Закрытие главного окна. Очистка 3D режима (если активен).")
        if self.opengl_process and self.opengl_process.is_alive():
            self.stop_3d_mode()
        # --- Close Debuggers on Main Window Close ---
        self.on_debugger_close() # Close line debugger
        self.on_vd_debugger_close() # Close V/D debugger
        # -------------------------------------------
        self.root.destroy()

    # --- Apply Transformation Methods ---

    def apply_translate_2d(self):
        if self.selected_item_index is None or self.selected_handle_index is not None:
            print("Ошибка: Элемент не выбран для перемещения (или выбрана ручка).")
            return
        try:
            dx = self.translate_x_var.get()
            dy = self.translate_y_var.get()
        except tk.TclError: print("Ошибка: Неверное значение для перемещения."); return

        item = self.drawn_items[self.selected_item_index]
        if "points" not in item: return

        # Apply transformation to the points (hull points for polygons)
        original_points = [list(p) for p in item["points"]]
        new_points = translate_2d(original_points, dx, dy)

        if self.debug_mode_active.get():
            print(f"--- [Отладка 2D] Перемещение (Элемент {self.selected_item_index}, Тип {item.get('type')}) ---")
            print(f"  DX: {dx:.2f}, DY: {dy:.2f}")
            print(f"  Начальные точки: {[f'[{p[0]:.1f}, {p[1]:.1f}]' for p in original_points]}")
            print(f"  Конечные точки: {[f'[{p[0]:.1f}, {p[1]:.1f}]' for p in new_points]}")
            print("---------------------------------")

        item["points"] = new_points # Update stored points
        self.redraw_item(self.selected_item_index) # Redraw the item in new position
        self.translate_x_var.set(0.0)
        self.translate_y_var.set(0.0)

    def apply_rotate_2d(self):
        if self.selected_item_index is None or self.selected_handle_index is not None: return
        try: angle = self.rotate_angle_var.get()
        except tk.TclError: print("Ошибка: Неверное значение для угла поворота."); return

        item = self.drawn_items[self.selected_item_index]
        if "points" not in item or not item["points"]: return

        original_points = [list(p) for p in item["points"]]
        center_x, center_y = get_center(original_points)
        new_points = rotate_2d(original_points, angle, center_x, center_y)

        if self.debug_mode_active.get():
            print(f"--- [Отладка 2D] Поворот (Элемент {self.selected_item_index}, Тип {item.get('type')}) ---")
            print(f"  Угол: {angle:.2f} град.")
            print(f"  Центр: ({center_x:.1f}, {center_y:.1f})")
            print(f"  Начальные точки: {[f'[{p[0]:.1f}, {p[1]:.1f}]' for p in original_points]}")
            print(f"  Конечные точки: {[f'[{p[0]:.1f}, {p[1]:.1f}]' for p in new_points]}")
            print("-----------------------------")

        item["points"] = new_points
        self.redraw_item(self.selected_item_index)
        self.rotate_angle_var.set(0.0)

    def apply_scale_2d(self):
        if self.selected_item_index is None or self.selected_handle_index is not None: return
        try:
            sx = self.scale_x_var.get()
            sy = self.scale_y_var.get()
        except tk.TclError: print("Ошибка: Неверное значение для масштабирования."); return

        item = self.drawn_items[self.selected_item_index]
        if "points" not in item or not item["points"]: return

        original_points = [list(p) for p in item["points"]]
        center_x, center_y = get_center(original_points)
        new_points = scale_2d(original_points, sx, sy, center_x, center_y)

        if self.debug_mode_active.get():
            print(f"--- [Отладка 2D] Масштаб (Элемент {self.selected_item_index}, Тип {item.get('type')}) ---")
            print(f"  SX: {sx:.2f}, SY: {sy:.2f}")
            print(f"  Центр: ({center_x:.1f}, {center_y:.1f})")
            print(f"  Начальные точки: {[f'[{p[0]:.1f}, {p[1]:.1f}]' for p in original_points]}")
            print(f"  Конечные точки: {[f'[{p[0]:.1f}, {p[1]:.1f}]' for p in new_points]}")
            print("-----------------------------")

        item["points"] = new_points
        self.redraw_item(self.selected_item_index)
        self.scale_x_var.set(1.0)
        self.scale_y_var.set(1.0)

    # --- Методы для Анализа Полигонов ---

    def update_analysis_menu_state(self):
        """Активирует или деактивирует меню анализа, если есть полигоны."""
        has_polygons = any(item.get("type") == "polygon" for item in self.drawn_items)
        new_state = tk.NORMAL if has_polygons else tk.DISABLED
        if self.menu.entrycget("Анализ полигона", "state") != new_state:
            self.menu.entryconfig("Анализ полигона", state=new_state)
            # print(f"Меню 'Анализ полигона' теперь: {new_state}")

    def enter_polygon_analysis_mode(self, mode):
        """Вход в режим анализа полигонов."""
        # Сначала выходим из других режимов
        if self.edit_mode:
            self.deactivate_edit_tool()
        if self.active_context:
            self.active_context = None # Сбрасываем активный инструмент рисования
            # Скрываем кнопки, специфичные для инструментов (например, "Построить оболочку")
            if self.build_hull_button and self.build_hull_button.winfo_ismapped():
                self.build_hull_button.pack_forget()
        self.canvas_view.unbind_all() # Убираем все биндинги

        self.analysis_mode = mode
        self.selected_polygon_for_analysis_idx = None
        self.clear_analysis_feedback() # Очищаем старую визуализацию анализа

        # Привязываем клик для выбора полигона
        self.canvas_view.bind_event("<Button-1>", self.handle_analysis_click)
        print(f"Вход в режим анализа: {mode}. Кликните на полигон.")
        # Можно добавить статусную строку для подсказок пользователю

    def cancel_analysis_mode(self):
        """Выход из режима анализа полигонов."""
        if not self.analysis_mode: return
        print("Выход из режима анализа.")
        self.analysis_mode = None
        self.selected_polygon_for_analysis_idx = None
        self.clear_analysis_feedback()
        # Возвращаем биндинги предыдущего инструмента (если он был)
        if self.last_active_draw_context == self.line_context:
             self.activate_line_tool()
        elif self.last_active_draw_context == self.second_order_context:
             self.activate_second_order_tool()
        elif self.last_active_draw_context == self.curve_context:
             self.activate_curve_tool()
        elif self.last_active_draw_context == self.polygon_context:
             self.activate_polygon_tool()
        else:
             # Если не было активного инструмента, можно просто убрать биндинги
             # или вернуть режим редактирования, если он был до этого?
             # Пока просто очистим биндинги
             self.canvas_view.unbind_all()
             # self.activate_edit_tool() # Или так?

    def clear_analysis_feedback(self):
        """Удаляет временные элементы анализа с холста."""
        for item_id in self.analysis_feedback_items:
            try:
                self.canvas_view.canvas.delete(item_id)
            except tk.TclError:
                pass # Элемент уже мог быть удален
        self.analysis_feedback_items = []

    def find_polygon_at(self, x, y):
        """Находит индекс полигона в self.drawn_items под указанными координатами."""
        # Ищем полигон, к которому точка ближе всего (в пределах SNAP_RADIUS)
        # или для которого результат point_in_polygon != "outside"
        selected_idx = None
        min_dist_sq = self.SNAP_RADIUS**2

        for idx, item in enumerate(self.drawn_items):
            if item.get("type") == "polygon":
                points = item.get("points")
                if not points: continue

                # 1. Проверка близости к вершинам
                for p in points:
                    dist_sq = (x - p[0])**2 + (y - p[1])**2
                    if dist_sq <= min_dist_sq:
                        selected_idx = idx
                        min_dist_sq = dist_sq
                        break # Нашли близкую вершину для этого полигона

                # 2. Если не нашли по близости, проверим попадание внутрь или на границу
                if selected_idx is None:
                    # Используем point_in_polygon для более точного определения
                    # ВАЖНО: point_in_polygon медленнее, чем проверка расстояния
                    status = pa.point_in_polygon((x, y), points)
                    if status != "outside":
                        selected_idx = idx
                        break # Нашли полигон, в который попадает точка

                if selected_idx == idx and min_dist_sq == 0: break # Точное попадание в вершину

        return selected_idx

    def handle_analysis_click(self, event):
        """Обрабатывает клик мыши в режиме анализа."""
        if not self.analysis_mode:
            return

        x, y = self.canvas_view.get_coordinates(event)

        # Шаг 1: Выбор полигона (для всех режимов анализа)
        if self.selected_polygon_for_analysis_idx is None:
            clicked_polygon_idx = self.find_polygon_at(x, y)
            if clicked_polygon_idx is not None:
                self.selected_polygon_for_analysis_idx = clicked_polygon_idx
                item = self.drawn_items[clicked_polygon_idx]
                poly_points = item.get("points")
                print(f"Выбран полигон {clicked_polygon_idx} для анализа '{self.analysis_mode}'.")

                # Выполняем анализ или переходим к следующему шагу
                if self.analysis_mode == "check_convex":
                    is_conv = pa.is_convex(poly_points)
                    print(f"Полигон {clicked_polygon_idx} выпуклый: {is_conv}")
                    # Можно вывести сообщение в GUI
                    self.cancel_analysis_mode() # Завершаем режим
                elif self.analysis_mode == "show_normals":
                    normals = pa.get_inner_normals(poly_points)
                    self.draw_normals(normals)
                    print(f"Показаны нормали для полигона {clicked_polygon_idx}.")
                    # Нормали остаются до следующей очистки или выхода из режима
                    # Не выходим из режима сразу, чтобы можно было выбрать другой полигон
                    self.selected_polygon_for_analysis_idx = None # Готовы выбрать следующий
                    print(f"Кликните на следующий полигон или выберите другой инструмент/режим.")
                elif self.analysis_mode == "segment_intersection":
                    # Переходим в режим рисования отрезка
                    print("Теперь нарисуйте отрезок для проверки пересечения.")
                    self.analysis_mode = "draw_intersect_segment"
                    # Используем стандартные обработчики start/end_draw, но с другой логикой в end_draw
                    self.canvas_view.bind_event("<Button-1>", self.start_draw)
                elif self.analysis_mode == "point_in_polygon":
                    print("Теперь кликните точку для проверки принадлежности.")
                    self.analysis_mode = "pick_point_for_test"
                    # Клик обработается этим же методом handle_analysis_click в следующем вызове
                else:
                    self.cancel_analysis_mode()
            else:
                print("Полигон не найден в точке клика. Попробуйте еще раз.")

        # Шаг 2: Указание точки для проверки принадлежности
        elif self.analysis_mode == "pick_point_for_test":
            if self.selected_polygon_for_analysis_idx is not None:
                poly_points = self.drawn_items[self.selected_polygon_for_analysis_idx].get("points")
                status = pa.point_in_polygon((x, y), poly_points)
                print(f"Точка ({x}, {y}) находится '{status}' полигона {self.selected_polygon_for_analysis_idx}.")
                # Рисуем временную точку и ее статус
                self.draw_point_status((x, y), status)
                self.selected_polygon_for_analysis_idx = None # Сбрасываем выбор полигона
                self.analysis_mode = "point_in_polygon" # Возвращаемся к выбору полигона
                print(f"Кликните на полигон для следующей проверки или выберите другой инструмент/режим.")
            else:
                # Этого не должно произойти, но на всякий случай
                self.cancel_analysis_mode()

    def end_analysis_segment_draw(self, event):
        """Завершает рисование отрезка для анализа пересечения."""
        print(f"[DEBUG] end_analysis_segment_draw: Called. Mode={self.analysis_mode}, start_x={self.canvas_view.start_x}")
        if self.analysis_mode != "draw_intersect_segment" or self.canvas_view.start_x is None:
            print("[DEBUG] end_analysis_segment_draw: Condition failed, cancelling analysis.")
            self.cancel_analysis_mode() # Выход, если что-то пошло не так
            return

        end_x, end_y = self.canvas_view.get_coordinates(event)
        start_point = [self.canvas_view.start_x, self.canvas_view.start_y]
        end_point = [end_x, end_y]
        segment = (start_point, end_point)

        if self.selected_polygon_for_analysis_idx is not None:
            poly_points = self.drawn_items[self.selected_polygon_for_analysis_idx].get("points")
            intersections = pa.segment_intersects_polygon(start_point, end_point, poly_points)
            print(f"Найдено {len(intersections)} точек пересечения отрезка с полигоном {self.selected_polygon_for_analysis_idx}: {intersections}")

            # Отрисовка отрезка и точек пересечения
            self.draw_intersection_results(segment, intersections)

            self.selected_polygon_for_analysis_idx = None # Сбрасываем выбор полигона
            self.analysis_mode = "segment_intersection" # Возвращаемся к выбору полигона
            self.canvas_view.bind_event("<Button-1>", self.handle_analysis_click) # Восстанавливаем биндинг
            print(f"Кликните на полигон для следующей проверки или выберите другой инструмент/режим.")
        else:
            self.cancel_analysis_mode()

        # Сброс начальной точки для start_draw
        self.canvas_view.start_x = None
        self.canvas_view.start_y = None

    def draw_normals(self, normals):
        """Отрисовывает нормали на холсте."""
        self.clear_analysis_feedback() # Очищаем предыдущие
        canvas = self.canvas_view.canvas
        scale = 20 # Длина отображаемой нормали
        for mid_point, normal_vec in normals:
            x1, y1 = mid_point
            # Конечная точка нормали
            x2 = x1 + normal_vec[0] * scale
            y2 = y1 + normal_vec[1] * scale
            # Рисуем линию нормали
            line_id = canvas.create_line(x1, y1, x2, y2, fill="cyan", arrow=tk.LAST, width=1)
            self.analysis_feedback_items.append(line_id)
            # Маленький кружок в точке приложения
            # r = 2
            # circle_id = canvas.create_oval(x1-r, y1-r, x1+r, y1+r, fill="cyan", outline="")
            # self.analysis_feedback_items.append(circle_id)

    def draw_intersection_results(self, segment, intersections):
        """Отрисовывает отрезок и точки пересечения."""
        self.clear_analysis_feedback()
        canvas = self.canvas_view.canvas
        p1, p2 = segment
        # Рисуем сам тестовый отрезок
        seg_id = canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="orange", width=1, dash=(4, 2))
        self.analysis_feedback_items.append(seg_id)
        # Рисуем точки пересечения
        radius = 3
        for p in intersections:
            x, y = p
            point_id = canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="red", outline="red")
            self.analysis_feedback_items.append(point_id)

    def draw_point_status(self, point, status):
        """Отрисовывает тестовую точку и ее статус."""
        self.clear_analysis_feedback()
        canvas = self.canvas_view.canvas
        x, y = point
        radius = 3
        color = "green" if status == "inside" else ("blue" if status == "boundary" else "red")
        outline_color = color

        # Рисуем точку
        point_id = canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, outline=outline_color)
        self.analysis_feedback_items.append(point_id)
        # Добавляем текст статуса рядом
        text_id = canvas.create_text(x + 5, y - 5, text=status, fill=color, anchor=tk.W)
        self.analysis_feedback_items.append(text_id)

    # --- Методы для Заливки Полигонов ---

    def cancel_fill_mode(self):
        """Отменяет текущий режим заливки."""
        if self.fill_mode:
            print("Отмена режима заливки.")
            self.fill_mode = None
            self.selected_polygon_for_fill_idx = None
            # self.clear_fill_feedback() # Не нужно, т.к. используем теги или image
            # Возвращаем стандартное поведение клика (если оно было изменено)
            # Возможно, лучше переключиться на инструмент по умолчанию или режим редактирования?
            if self.last_active_draw_context:
                 self.active_context = self.last_active_draw_context
                 # Восстановить биндинги для этого контекста?
                 # self.activate_draw_tool_common(...) # Пример
            else:
                # Если нет предыдущего контекста, возможно, активировать инструмент по умолчанию
                self.activate_line_tool() # Например

    def clear_fill_feedback(self):
        """Удаляет элементы заливки с холста (старый метод, больше не нужен)."""
        # Этот метод больше не нужен в таком виде, т.к. ET+AEL использует теги,
        # а PIL-заливка управляется через current_fill_photo_image и canvas.fill_image_id
        print("[INFO] clear_fill_feedback() больше не используется активно.")
        pass

    def handle_fill_click(self, event):
        """Обрабатывает клик мыши в режиме заливки."""
        if not self.fill_mode:
            print("[DEBUG] handle_fill_click called but fill_mode is None. Ignoring.")
            return

        x, y = self.canvas_view.get_coordinates(event)
        strategy = self.fill_context.get_strategy()
        if not strategy:
            print("Ошибка: Стратегия заливки не выбрана.")
            self.cancel_fill_mode() # Exit if no strategy
            return

        # Шаг 1: Выбор полигона
        if self.fill_mode == "select_polygon":
            clicked_polygon_idx = self.find_polygon_at(x, y)
            if clicked_polygon_idx is not None:
                self.selected_polygon_for_fill_idx = clicked_polygon_idx
                print(f"Выбран полигон {clicked_polygon_idx} для заливки.")
                poly_item = self.drawn_items[self.selected_polygon_for_fill_idx]

                if poly_item.get("type") != "polygon":
                     print(f"Ошибка: Выбранный элемент ({poly_item.get('type')}) не является полигоном.")
                     self.selected_polygon_for_fill_idx = None
                     return # Stay in select_polygon mode

                # --- Clear previous fills --- 
                canvas = self.canvas_view.canvas
                if hasattr(canvas, 'fill_image_id'):
                    try: canvas.delete(canvas.fill_image_id)
                    except tk.TclError: pass
                    del canvas.fill_image_id
                self.current_fill_photo_image = None
                old_fill_tag = poly_item.get("fill_tag")
                if old_fill_tag:
                    canvas.delete(old_fill_tag)
                    del poly_item["fill_tag"]
                # --------------------------

                # --- Proceed based on strategy type --- 
                if not strategy.requires_seed:
                    # --- Execute No-Seed Fill (e.g., ET+AEL) --- 
                    print(f"Запуск {strategy.name} для полигона {clicked_polygon_idx}...")
                    try:
                        rgb_tuple = canvas.winfo_rgb(self.fill_color)
                        hex_fill_color = f'#{rgb_tuple[0]//256:02x}{rgb_tuple[1]//256:02x}{rgb_tuple[2]//256:02x}'
                    except tk.TclError:
                        hex_fill_color = '#000000'
                    poly_points = poly_item.get("points")
                    fill_tag = self.fill_context.execute_strategy(canvas, poly_points, hex_fill_color)
                    if fill_tag:
                        poly_item["fill_tag"] = fill_tag
                        print(f"{strategy.name} завершен. Тег заливки: {fill_tag}")
                    else: print(f"{strategy.name} не выполнен.")
                    # --- Reset for next selection --- 
                    self.selected_polygon_for_fill_idx = None
                    # Stay in select_polygon mode
                    print("Кликните на следующий полигон или выберите другой инструмент.")
                else:
                    # --- Transition to Seed Picking --- 
                    if Image is None:
                         print("Ошибка: Pillow не установлен. Невозможно выполнить заливку с затравкой.")
                         self.selected_polygon_for_fill_idx = None
                         return # Stay in select_polygon mode
                    
                    # Check if click was roughly within polygon bbox (optional, good UX)
                    bbox = canvas.bbox(poly_item["tag"]) 
                    if bbox and not (bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]):
                         print("Клик вне ограничивающего прямоугольника полигона. Выберите полигон снова.")
                         self.selected_polygon_for_fill_idx = None
                         return # Stay in select_polygon mode
                    
                    # Transition state
                    self.fill_mode = "pick_seed"
                    print("Теперь кликните ВНУТРИ полигона для точки затравки.")
                    # The SAME click handler (handle_fill_click) will process the next click
            else:
                print("Полигон не найден в точке клика. Попробуйте еще раз.")

        # Шаг 2: Выбор точки затравки (для Flood/Scanline)
        elif self.fill_mode == "pick_seed":
            if self.selected_polygon_for_fill_idx is None:
                 print("[WARN] pick_seed mode active but no polygon selected. Resetting.")
                 self.fill_mode = "select_polygon"
                 return
            
            if Image is None: # Should have been caught earlier, but double-check
                 print("Ошибка: Pillow не установлен.")
                 self.cancel_fill_mode()
                 return
            
            print(f"Обработка клика ({x},{y}) как точки затравки для полигона {self.selected_polygon_for_fill_idx}")
            poly_item = self.drawn_items[self.selected_polygon_for_fill_idx]
            poly_points = poly_item.get("points")
            canvas = self.canvas_view.canvas

            # --- Check if click is INSIDE the polygon --- 
            status = pa.point_in_polygon((x, y), poly_points)
            if status != "inside":
                print(f"Точка ({x},{y}) находится '{status}'. Кликните строго ВНУТРИ полигона для затравки.")
                # DO NOT reset state here, allow user to try clicking again
                return
            # -------------------------------------------

            # --- Prepare PIL Image --- 
            canvas.update_idletasks()
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            if width <= 0 or height <= 0:
                 print("Ошибка: Не удалось получить размеры холста.")
                 self.cancel_fill_mode()
                 return
            try:
                bg_color = canvas.cget('bg')
                pil_bg_color = self._hex_to_rgb_pil(bg_color) if bg_color else (255, 255, 255)
            except Exception:
                pil_bg_color = (255, 255, 255)
            pil_image = Image.new('RGB', (width, height), pil_bg_color)
            draw = ImageDraw.Draw(pil_image)
            boundary_color_pil = (0, 0, 0) # Assuming black boundary for PIL fill logic
            pil_poly_points = [(int(px), int(py)) for px, py in poly_points]
            if len(pil_poly_points) > 1:
                draw.line(pil_poly_points + [pil_poly_points[0]], fill=boundary_color_pil, width=1)
            del draw
            # -------------------------

            # --- Get Fill Color --- 
            try:
                rgb_tuple = canvas.winfo_rgb(self.fill_color)
                hex_fill_color = f'#{rgb_tuple[0]//256:02x}{rgb_tuple[1]//256:02x}{rgb_tuple[2]//256:02x}'
            except tk.TclError:
                hex_fill_color = '#000000'
            # ---------------------

            # --- Execute Seed Fill --- 
            print(f"Точка затравки: ({x},{y}). Запуск {strategy.name}...")
            result_image = self.fill_context.execute_strategy(
                canvas, poly_points, hex_fill_color,
                seed_point=(int(x), int(y)),
                image=pil_image
            )
            # -----------------------

            # --- Display Result --- 
            if isinstance(result_image, Image.Image):
                print(f"{strategy.name} завершен. Отображение результата...")
                self.current_fill_photo_image = ImageTk.PhotoImage(result_image)
                canvas.fill_image_id = canvas.create_image(0, 0, anchor=tk.NW, image=self.current_fill_photo_image, tags="fill_image")
                canvas.tag_raise(poly_item["tag"])
                handles = canvas.find_withtag(f"handle_{poly_item['tag']}_")
                for handle_id in handles:
                     canvas.tag_raise(handle_id)
            else:
                print(f"{strategy.name} не вернул изображение. Заливка не удалась.")
            # --------------------

            # --- Reset state AFTER successful/attempted fill --- 
            self.selected_polygon_for_fill_idx = None
            self.fill_mode = "select_polygon" # Go back to selecting polygons
            print("Заливка выполнена (или предпринята попытка). Кликните на следующий полигон или выберите другой инструмент.")
            # --------------------------------------------------

    def _hex_to_rgb_pil(self, hex_color):
        """Преобразует HEX цвет Tkinter в RGB кортеж для PIL."""
        try:
            hex_color = hex_color.lstrip('#')
            # Tkinter может возвращать '#RRGGBB' или по имени 'white'
            # PIL ожидает (R, G, B)
            if len(hex_color) == 6:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            else:
                 # Пытаемся получить RGB из стандартных имен цветов Tkinter
                 # Это требует root окна для colormapfromstring
                 rgb_tuple = self.root.winfo_rgb(hex_color)
                 # winfo_rgb возвращает 16-битные значения, конвертируем в 8-битные
                 return tuple(c // 256 for c in rgb_tuple)
        except Exception as e:
            print(f"Предупреждение: Не удалось преобразовать цвет '{hex_color}' в RGB: {e}. Используется белый.")
            return (255, 255, 255) # По умолчанию белый

    def choose_fill_color(self):
        """Открывает диалог выбора цвета и сохраняет результат в self.fill_color."""
        color_code = colorchooser.askcolor(title="Выберите цвет заливки", initialcolor=self.fill_color)
        if color_code and color_code[1]: # color_code[1] это hex цвет
            self.fill_color = color_code[1]
            print(f"Выбран цвет заливки: {self.fill_color}")
        else:
            print("Выбор цвета отменен.")

    # --- Voronoi/Delaunay Tool Activation ---
    def activate_voronoi_delaunay_tool(self):
        """Активирует инструмент ввода точек для диаграмм Вороного/триангуляции Делоне."""
        self.activate_draw_tool_common(self.voronoi_delaunay_context, click_handler=self.capture_vd_point)
        print(f"{self.voronoi_delaunay_context.get_current_strategy_name()} tool activated. Click to add points.")

        # Очищаем предыдущие точки ввода V/D и результаты
        self.clear_vd_input_points()
        self.clear_vd_results()
        self.vd_input_points = [] # Reset logical points array

        # Показываем кнопку "Построить"
        if self.build_vd_button:
            # Pack before the clear button instead of the potentially hidden transform frame
            self.build_vd_button.pack(pady=5, fill=tk.X, before=self.clear_button)
            self.build_vd_button.config(state=tk.DISABLED) # Initially disabled

        # Скрываем кнопку построения оболочки
        if self.build_hull_button:
            self.build_hull_button.pack_forget()
    # ----------------------------------------

    def capture_vd_point(self, event):
        """Захватывает точку для Вороного/Делоне и отображает ее."""
        x, y = event.x, event.y
        self.vd_input_points.append((x, y))

        # Draw a temporary visual representation of the point
        r = self.TEMP_VD_POINT_RADIUS
        point_id = self.canvas_view.canvas.create_oval(x - r, y - r, x + r, y + r, fill="red", outline="red", tags="vd_temp_point")
        self.vd_temp_point_ids.append(point_id)

        # Enable the build button if enough points are available
        min_points = 3 if "Делоне" in self.voronoi_delaunay_context.get_current_strategy_name() else 2
        if len(self.vd_input_points) >= min_points:
            if self.build_vd_button:
                self.build_vd_button.config(state=tk.NORMAL)

    def build_voronoi_delaunay(self):
        """Вычисляет и отрисовывает диаграмму Вороного или триангуляцию Делоне.
           Запускает отладчик, если включен режим отладки V/D.
        """
        if not self.voronoi_delaunay_context or not self.voronoi_delaunay_context.strategy:
            print("Ошибка: Не выбран алгоритм Вороного/Делоне.")
            return

        # Determine minimum points based on the actual strategy class
        strategy_class = type(self.voronoi_delaunay_context.strategy)
        is_delaunay = "DelaunayStrategy" in str(strategy_class)
        min_points = 3 if is_delaunay else 2

        if len(self.vd_input_points) < min_points:
            print(f"Ошибка: Необходимо как минимум {min_points} точки для {self.voronoi_delaunay_context.get_current_strategy_name()}.")
            return

        # --- Check for Debug Mode --- 
        if self.vd_debug_mode_active.get():
            print(f"Запуск отладчика для {self.voronoi_delaunay_context.get_current_strategy_name()}...")
            if self.vd_debugger and self.vd_debugger.debug_window.winfo_exists():
                print("Отладчик V/D уже открыт. Закройте его сначала.")
                return
            # Pass context and points to the debugger
            self.vd_debugger = VoronoiDelaunayDebugger(
                self.root,
                self.voronoi_delaunay_context,
                list(self.vd_input_points) # Pass a copy
            )
            # Set the close protocol for the debugger window
            if self.vd_debugger and self.vd_debugger.debug_window:
                 self.vd_debugger.debug_window.protocol("WM_DELETE_WINDOW", self.on_vd_debugger_close)
            # Don't draw on main canvas or clear results here, debugger handles visualization
            if self.build_vd_button:
                 self.build_vd_button.config(state=tk.DISABLED)
            return # Exit after launching debugger
        # --------------------------

        # --- Normal Execution (No Debug Mode) ---
        print(f"Building {self.voronoi_delaunay_context.get_current_strategy_name()} with {len(self.vd_input_points)} points.")

        # Clear previous results from main canvas
        self.clear_vd_results()

        # Execute computation (using the normal compute method)
        result = self.voronoi_delaunay_context.execute_compute(self.vd_input_points)

        if result:
            # Execute drawing on main canvas
            self.vd_result_ids = self.voronoi_delaunay_context.execute_draw(
                self.canvas_view.canvas,
                self.vd_input_points,
                result
            )
            print(f"Drawn {len(self.vd_result_ids)} elements on main canvas.")
        else:
            print("Computation failed or returned no result.")

        # Keep input points visible, disable build button until more points added
        if self.build_vd_button:
            self.build_vd_button.config(state=tk.DISABLED)

    def clear_vd_input_points(self):
        """Удаляет временные точки ввода V/D с холста."""
        for item_id in self.vd_temp_point_ids:
            self.canvas_view.canvas.delete(item_id)
        self.vd_temp_point_ids = []
        # Keep self.vd_input_points logical array until a new tool is selected or clear is called

    def clear_vd_results(self):
        """Удаляет отрисованные элементы V/D с холста."""
        for item_id in self.vd_result_ids:
            self.canvas_view.canvas.delete(item_id)
        self.vd_result_ids = []

    # --- V/D Debugger Toggle and Cleanup ---
    def toggle_vd_debug(self):
        """Включает/выключает режим отладки V/D."""
        if self.vd_debug_mode_active.get():
            print("[Отладка V/D ВКЛЮЧЕНА (пошаговый режим)]")
        else:
            print("[Отладка V/D ВЫКЛЮЧЕНА]")
            # Close debugger if it's open when mode is turned off
            self.on_vd_debugger_close()

    def on_vd_debugger_close(self):
        """Callback or manual close for V/D debugger window."""
        if self.vd_debugger and self.vd_debugger.debug_window.winfo_exists():
            # Prevent recursive close if called from window protocol
            self.vd_debugger.debug_window.protocol("WM_DELETE_WINDOW", lambda: None)
            self.vd_debugger.on_close() # Use the debugger's close method
        self.vd_debugger = None
        # Optionally, uncheck the menu item if closed manually
        # self.vd_debug_mode_active.set(False)
    # -------------------------------------
