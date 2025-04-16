# model/fill_algorithms.py
from abc import ABC, abstractmethod
import tkinter as tk
import time
from collections import defaultdict
import math

class FillStrategyInterface(ABC):
    """Интерфейс для алгоритмов заливки полигонов."""
    @abstractmethod
    def __init__(self):
        self.name = "Unknown Fill Algorithm"
        self.requires_seed = False # Указывает, нужен ли клик для точки затравки

    @abstractmethod
    def fill(self, canvas: tk.Canvas, polygon_points: list, fill_color: str, **kwargs):
        """
        Выполняет заливку полигона.

        Args:
            canvas (tk.Canvas): Холст для отрисовки.
            polygon_points (list[tuple[int, int]]): Список вершин полигона.
            fill_color (str): Цвет заливки (например, 'red', '#FF0000').
            **kwargs: Дополнительные аргументы (например, seed_point для алгоритмов с затравкой).

        Returns:
            str: Тег для созданных элементов заливки (или None).
        """
        pass

    def _plot_pixel(self, canvas: tk.Canvas, x: int, y: int, color: str, tag: str):
        """Вспомогательный метод для отрисовки 'пикселя'."""
        # Рисуем квадрат 1x1
        canvas.create_rectangle(x, y, x + 1, y + 1, fill=color, outline=color, tags=tag)

# --- Алгоритм Edge Table + Active Edge List ---
class ET_AEL_FillStrategy(FillStrategyInterface):
    def __init__(self):
        self.name = "ET + AEL Scanline"
        self.requires_seed = False

    def fill(self, canvas: tk.Canvas, polygon_points: list, fill_color: str, **kwargs):
        if not polygon_points or len(polygon_points) < 3:
            return None

        fill_tag = f"fill_et_ael_{time.time_ns()}"
        # 1. Определить Y_min и Y_max полигона
        min_y = min(p[1] for p in polygon_points)
        max_y = max(p[1] for p in polygon_points)

        # 2. Создать Edge Table (ET)
        edge_table = defaultdict(list)
        n = len(polygon_points)
        for i in range(n):
            p1 = polygon_points[i]
            p2 = polygon_points[(i + 1) % n]
            y1, y2 = p1[1], p2[1]
            x1, x2 = p1[0], p2[0]

            # Игнорируем горизонтальные ребра
            if y1 == y2:
                continue

            # Упорядочиваем точки по Y
            if y1 > y2:
                y1, y2 = y2, y1
                x1, x2 = x2, x1

            # Параметры ребра для AEL
            slope_inv = (x2 - x1) / (y2 - y1) if (y2 - y1) != 0 else 0
            edge_entry = {'y_max': y2, 'x_current': float(x1), 'slope_inv': slope_inv}
            edge_table[y1].append(edge_entry)

        # 3. Инициализировать Active Edge List (AEL)
        active_edge_list = []

        # 4. Цикл по строкам развертки (scanlines)
        for y in range(min_y, max_y + 1):
            # Удаляем ребра из AEL, для которых y == y_max
            active_edge_list = [edge for edge in active_edge_list if edge['y_max'] > y]

            # Добавляем ребра из ET в AEL, для которых y == y_min
            if y in edge_table:
                active_edge_list.extend(edge_table[y])

            # Сортируем AEL по x_current
            active_edge_list.sort(key=lambda edge: edge['x_current'])

            # Заполняем пиксели между парами ребер в AEL
            for i in range(0, len(active_edge_list), 2):
                if i + 1 < len(active_edge_list):
                    x_start = math.ceil(active_edge_list[i]['x_current'])
                    x_end = math.floor(active_edge_list[i+1]['x_current'])
                    for x in range(x_start, x_end + 1):
                        self._plot_pixel(canvas, x, y, fill_color, fill_tag)

            # Обновляем x_current для следующей строки
            for edge in active_edge_list:
                edge['x_current'] += edge['slope_inv']

        return fill_tag

# --- Алгоритм Flood Fill (простой) ---
class FloodFillStrategy(FillStrategyInterface):
    def __init__(self):
        self.name = "Flood Fill (Simple)"
        self.requires_seed = True

    def fill(self, canvas: tk.Canvas, polygon_points: list, fill_color: str, **kwargs):
        seed_point = kwargs.get('seed_point')
        if not seed_point:
            print("Ошибка: Flood Fill требует точки затравки (seed_point).")
            return None

        # Flood fill крайне неэффективен с create_rectangle в Tkinter.
        # Нужен доступ к пикселям напрямую (через Pillow или другую библиотеку)
        # или очень простая геометрия.
        # Здесь будет ПСЕВДОКОД/заглушка, т.к. реализация на canvas очень медленная.
        print("Предупреждение: Flood Fill на Canvas очень медленный и не реализован.")
        print(f"  Запрошена заливка цветом {fill_color} от точки {seed_point}")
        fill_tag = f"fill_flood_{time.time_ns()}"
        # TODO: Реализовать с использованием Pillow Image + ImageTk или аналога
        # 1. Получить цвет пикселя в seed_point (target_color)
        # 2. Если target_color == fill_color или target_color == boundary_color, выход.
        # 3. Использовать стек или очередь:
        #    - Добавить seed_point в стек.
        #    - Пока стек не пуст:
        #        - Извлечь точку (x, y).
        #        - Если цвет(x,y) == target_color:
        #            - Установить цвет(x,y) = fill_color
        #            - Добавить соседей (x+1, y), (x-1, y), (x, y+1), (x, y-1) в стек.

        # Временная визуализация точки затравки
        sx, sy = map(int, seed_point)
        canvas.create_oval(sx-2, sy-2, sx+2, sy+2, fill=fill_color, outline=fill_color, tags=fill_tag)

        return fill_tag # Возвращаем тег, хотя заливки нет

# --- Алгоритм Scanline Seed Fill ---
class ScanlineSeedFillStrategy(FillStrategyInterface):
    def __init__(self):
        self.name = "Scanline Seed Fill"
        self.requires_seed = True

    def fill(self, canvas: tk.Canvas, polygon_points: list, fill_color: str, **kwargs):
        seed_point = kwargs.get('seed_point')
        if not seed_point:
            print("Ошибка: Scanline Seed Fill требует точки затравки (seed_point).")
            return None

        # Как и Flood Fill, требует эффективного доступа к пикселям.
        print("Предупреждение: Scanline Seed Fill на Canvas очень медленный и не реализован.")
        print(f"  Запрошена заливка цветом {fill_color} от точки {seed_point}")
        fill_tag = f"fill_scanline_seed_{time.time_ns()}"
        # TODO: Реализовать с использованием Pillow Image + ImageTk или аналога
        # 1. Получить цвет пикселя в seed_point (target_color)
        # 2. Если target_color == fill_color или target_color == boundary_color, выход.
        # 3. Использовать стек:
        #    - Добавить seed_point в стек.
        #    - Пока стек не пуст:
        #        - Извлечь точку (x_seed, y_seed).
        #        - Найти левую границу x_left и правую границу x_right для горизонтального отрезка
        #          одного цвета (target_color) на строке y_seed, содержащего x_seed.
        #        - Закрасить отрезок [x_left, x_right] на строке y_seed цветом fill_color.
        #        - Проверить строку y_seed + 1: найти на ней интервалы цвета target_color,
        #          частично или полностью находящиеся над закрашенным отрезком [x_left, x_right].
        #          Для каждого такого интервала добавить одну затравку (например, самую левую точку) в стек.
        #        - Аналогично проверить строку y_seed - 1 и добавить затравки в стек.

        # Временная визуализация точки затравки
        sx, sy = map(int, seed_point)
        canvas.create_oval(sx-2, sy-2, sx+2, sy+2, fill=fill_color, outline=fill_color, tags=fill_tag)
        return fill_tag

# --- Класс-заглушка для ET (демонстрация) ---
# (Алгоритм ET без AEL менее эффективен и обычно не используется отдельно в такой форме)
class ET_FillStrategy(FillStrategyInterface):
    def __init__(self):
        self.name = "ET Scanline (Simple)"
        self.requires_seed = False

    def fill(self, canvas: tk.Canvas, polygon_points: list, fill_color: str, **kwargs):
         # Реализация была бы похожа на ET+AEL, но без AEL, что делает
         # определение пар для заливки на каждой строке сложнее.
         print("Предупреждение: Простой ET алгоритм не реализован (используйте ET+AEL).")
         return None


# --- Контекст и Меню (можно вынести в отдельный файл) ---
class FillContext:
    """Контекст для выбора и выполнения стратегии заливки."""
    def __init__(self):
        self.__strategy: FillStrategyInterface = None
        self.strategies = {
            "ET + AEL Scanline": ET_AEL_FillStrategy(),
            "Flood Fill (Simple)": FloodFillStrategy(),
            "Scanline Seed Fill": ScanlineSeedFillStrategy(),
            # "ET Scanline (Simple)": ET_FillStrategy(), # Скрываем менее полезный
        }
        # Устанавливаем стратегию по умолчанию
        self.set_strategy("ET + AEL Scanline")

    def set_strategy(self, strategy_name: str):
        if strategy_name in self.strategies:
            self.__strategy = self.strategies[strategy_name]
            print(f"Выбрана стратегия заливки: {strategy_name}")
        else:
            print(f"Ошибка: Стратегия заливки '{strategy_name}' не найдена.")

    def get_strategy(self) -> FillStrategyInterface:
        return self.__strategy

    def get_available_strategies(self) -> list[str]:
        return list(self.strategies.keys())

    def execute_strategy(self, canvas, polygon_points, fill_color, **kwargs):
        if self.__strategy:
            print(f"Запуск стратегии заливки '{self.__strategy.name}'...")
            start_time = time.time()
            tag = self.__strategy.fill(canvas, polygon_points, fill_color, **kwargs)
            end_time = time.time()
            if tag:
                 print(f"Стратегия '{self.__strategy.name}' завершена за {end_time - start_time:.4f} сек.")
            else:
                 print(f"Стратегия '{self.__strategy.name}' не выполнена.")
            return tag
        else:
            print("Ошибка: Стратегия заливки не установлена.")
            return None

class FillMenuClass:
    """Класс для создания меню выбора алгоритмов заливки."""
    def __init__(self, root, button, context: FillContext, activate_tool_callback):
        self.root = root
        self.button = button
        self.context = context
        self.activate_tool_callback = activate_tool_callback # Функция для активации инструмента заливки
        self.algorithm_menu = tk.Menu(self.root, tearoff=0)

        available_strategies = self.context.get_available_strategies()
        for algo_name in available_strategies:
            self.algorithm_menu.add_command(
                label=algo_name,
                command=lambda name=algo_name: self.select_algorithm(name)
            )

    def select_algorithm(self, name):
        print(f"Выбран алгоритм заливки через меню: {name}")
        self.context.set_strategy(name)
        # Активируем инструмент заливки ПОСЛЕ выбора алгоритма
        self.activate_tool_callback()

    def show_algorithm_menu(self):
        self.algorithm_menu.post(self.button.winfo_rootx(), self.button.winfo_rooty() + self.button.winfo_height()) 