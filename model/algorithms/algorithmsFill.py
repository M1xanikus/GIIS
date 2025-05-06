# model/fill_algorithms.py
from abc import ABC, abstractmethod
import tkinter as tk
import time
from collections import defaultdict, deque
import math
try:
    from PIL import Image, ImageDraw, ImageTk
except ImportError:
    print("ОШИБКА: Для работы алгоритмов заливки Flood Fill и Scanline Seed Fill")
    print("        необходима библиотека Pillow. Установите ее: pip install Pillow")
    Image = None
    ImageDraw = None
    ImageTk = None

class FillStrategyInterface(ABC):
    """Интерфейс для алгоритмов заливки полигонов."""
    @abstractmethod
    def __init__(self):
        self.name = "Unknown Fill Algorithm"
        self.requires_seed = False # Указывает, нужен ли клик для точки затравки

    @abstractmethod
    def fill(self, canvas: tk.Canvas, polygon_points: list, fill_color: str, **kwargs):
        pass

    def _plot_pixel(self, canvas: tk.Canvas, x: int, y: int, color: str, tag: str):
        """Вспомогательный метод для отрисовки 'пикселя' на холсте (для ET+AEL)."""
        canvas.create_rectangle(x, y, x + 1, y + 1, fill=color, outline=color, tags=tag)

    def _hex_to_rgb(self, hex_color):
        """Преобразует HEX цвет (например, '#FF0000') в RGB кортеж (255, 0, 0)."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# --- Алгоритм Edge Table + Active Edge List ---
class ET_AEL_FillStrategy(FillStrategyInterface):
    def __init__(self):
        self.name = "Растровая развертка с ET и AEL"
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
            # Проверяем деление на ноль явно
            delta_y = y2 - y1
            if delta_y == 0: continue # Повторная проверка, на всякий случай
            slope_inv = (x2 - x1) / delta_y
            edge_entry = {'y_max': y2, 'x_current': float(x1), 'slope_inv': slope_inv}
            edge_table[y1].append(edge_entry)


        # 3. Инициализировать Active Edge List (AEL)
        active_edge_list = []

        # 4. Цикл по строкам развертки (scanlines)
        for y in range(min_y, max_y + 1):
            # Удаляем ребра из AEL, для которых y >= y_max (строго > в оригинале, но >= безопаснее для горизонталей)
            active_edge_list = [edge for edge in active_edge_list if edge['y_max'] > y]


            # Добавляем ребра из ET в AEL, для которых y == y_min
            if y in edge_table:
                active_edge_list.extend(edge_table[y])

            # Сортируем AEL по x_current
            active_edge_list.sort(key=lambda edge: edge['x_current'])

            # Заполняем пиксели между парами ребер в AEL
            for i in range(0, len(active_edge_list), 2):
                if i + 1 < len(active_edge_list):
                    # Округляем правильно: начало - ceil, конец - floor
                    x_start = math.ceil(active_edge_list[i]['x_current'])
                    # Конец должен быть включительно, но range не включает верхнюю границу,
                    # floor может дать тот же пиксель, что и ceil при малых наклонах
                    x_end = math.floor(active_edge_list[i+1]['x_current'])
                    for x in range(x_start, x_end + 1): # +1 чтобы включить x_end
                         # Проверяем границы холста перед отрисовкой
                         # canvas_width = canvas.winfo_width()
                         # canvas_height = canvas.winfo_height()
                         # if 0 <= x < canvas_width and 0 <= y < canvas_height:
                         self._plot_pixel(canvas, x, y, fill_color, fill_tag)


            # Обновляем x_current для следующей строки
            for edge in active_edge_list:
                edge['x_current'] += edge['slope_inv']

        return fill_tag

# --- Алгоритм Flood Fill (4-связный) ---
class FloodFillStrategy(FillStrategyInterface):
    def __init__(self):
        self.name = "Простой алгоритм с затравкой"
        self.requires_seed = True

    def fill(self, canvas: tk.Canvas, polygon_points: list, fill_color: str, **kwargs):
        if Image is None:
            print("Ошибка: Pillow не установлен.")
            return None

        seed_point = kwargs.get('seed_point')
        image: Image.Image = kwargs.get('image') # Ожидаем PIL Image

        if not seed_point or image is None:
            print(f"Ошибка: {self.name} требует 'seed_point' и 'image' (PIL.Image).")
            return None

        width, height = image.size
        sx, sy = map(int, seed_point)

        if not (0 <= sx < width and 0 <= sy < height):
            print("Ошибка: Точка затравки вне границ изображения.")
            return None

        target_color = image.getpixel((sx, sy))
        fill_color_rgb = self._hex_to_rgb(fill_color)

        if target_color == fill_color_rgb:
            print("Информация: Область уже залита нужным цветом.")
            return image # Возвращаем неизмененное изображение

        # Используем deque для эффективности как стек/очередь
        q = deque([(sx, sy)])
        pixels = image.load() # Доступ к пикселям для быстрой модификации

        while q:
            x, y = q.popleft() # или pop() для DFS-подобного поведения

            if not (0 <= x < width and 0 <= y < height):
                continue

            current_color = pixels[x, y]

            if current_color == target_color:
                pixels[x, y] = fill_color_rgb
                # Добавляем соседей (4-связность)
                q.append((x + 1, y))
                q.append((x - 1, y))
                q.append((x, y + 1))
                q.append((x, y - 1))

        return image # Возвращаем измененное изображение

# --- Алгоритм Scanline Seed Fill ---
class ScanlineSeedFillStrategy(FillStrategyInterface):
    def __init__(self):
        self.name = "Построчный алгоритм с затравкой"
        self.requires_seed = True

    def fill(self, canvas: tk.Canvas, polygon_points: list, fill_color: str, **kwargs):
        if Image is None:
            print("Ошибка: Pillow не установлен.")
            return None

        seed_point = kwargs.get('seed_point')
        image: Image.Image = kwargs.get('image')

        if not seed_point or image is None:
            print(f"Ошибка: {self.name} требует 'seed_point' и 'image' (PIL.Image).")
            return None

        width, height = image.size
        sx, sy = map(int, seed_point)

        if not (0 <= sx < width and 0 <= sy < height):
            print("Ошибка: Точка затравки вне границ изображения.")
            return None

        pixels = image.load()
        target_color = pixels[sx, sy]
        fill_color_rgb = self._hex_to_rgb(fill_color)

        if target_color == fill_color_rgb:
            print("Информация: Область уже залита нужным цветом.")
            return image

        # Стек для хранения затравочных точек (x, y)
        stack = [(sx, sy)]

        while stack:
            x, y = stack.pop()

            # Проверяем, не вышли ли за границы и не был ли пиксель уже обработан
            # (хотя проверка target_color ниже должна это покрывать)
            if not (0 <= y < height):
                 continue

            # 1. Идем влево от затравки до границы или другого цвета
            x_left = x
            while x_left >= 0 and pixels[x_left, y] == target_color:
                pixels[x_left, y] = fill_color_rgb
                x_left -= 1
            x_left += 1 # Вернуться к первому закрашенному пикселю

            # 2. Идем вправо от затравки (не включая ее) до границы или другого цвета
            x_right = x + 1
            while x_right < width and pixels[x_right, y] == target_color:
                pixels[x_right, y] = fill_color_rgb
                x_right += 1
            # x_right теперь указывает на первый пиксель *справа* от закрашенного интервала

            # 3. Проверяем строку выше (y + 1) на наличие новых затравок
            if y + 1 < height:
                self._check_scanline(pixels, width, target_color, x_left, x_right - 1, y + 1, stack)

            # 4. Проверяем строку ниже (y - 1) на наличие новых затравок
            if y - 1 >= 0:
                self._check_scanline(pixels, width, target_color, x_left, x_right - 1, y - 1, stack)

        return image

    def _check_scanline(self, pixels, width, target_color, x_min, x_max, y, stack):
        """
        Ищет новые затравочные пиксели на сканируемой строке y в диапазоне [x_min, x_max]
        и добавляет их в стек.
        """
        in_span = False
        for x in range(x_min, x_max + 1):
             # Проверяем границы x перед доступом к pixels
             if 0 <= x < width:
                pixel_color = pixels[x, y]
                if pixel_color == target_color:
                    # Если нашли пиксель целевого цвета и мы *не были* внутри сегмента,
                    # то это начало нового сегмента, добавляем затравку.
                    if not in_span:
                        stack.append((x, y))
                        in_span = True
                else:
                    # Если цвет не целевой, значит сегмент (если он был) закончился.
                    in_span = False
             else:
                 # Если вышли за границу по X, сегмент точно закончился
                 in_span = False


# --- Класс-заглушка для ET ---
class ET_FillStrategy(FillStrategyInterface):
    def __init__(self):
        self.name = "Сканлайн с ET (простой)"
        self.requires_seed = False

    def fill(self, canvas: tk.Canvas, polygon_points: list, fill_color: str, **kwargs):
        if not polygon_points or len(polygon_points) < 3:
            return None

        fill_tag = f"fill_et_simple_{time.time_ns()}"

        min_y = min(p[1] for p in polygon_points)
        max_y = max(p[1] for p in polygon_points)

        # --- Создание Edge Table (ET) --- 
        # В отличие от ET+AEL, храним больше информации для вычисления пересечений на каждой строке
        edge_table_full = []
        n = len(polygon_points)
        for i in range(n):
            p1 = polygon_points[i]
            p2 = polygon_points[(i + 1) % n]
            y1, y2 = p1[1], p2[1]
            x1, x2 = p1[0], p2[0]

            # Игнорируем горизонтальные ребра
            if y1 == y2:
                continue

            # Упорядочиваем точки по Y для удобства
            if y1 > y2:
                y1, y2 = y2, y1
                x1, x2 = x2, x1

            # Проверяем деление на ноль
            delta_y = y2 - y1
            if delta_y == 0: continue
            slope_inv = (x2 - x1) / delta_y

            # Сохраняем y_min, y_max, x_at_y_min, slope_inv
            edge_table_full.append({'y_min': y1, 'y_max': y2, 'x_at_y_min': float(x1), 'slope_inv': slope_inv})
        # --------------------------------

        # --- Цикл по строкам развертки --- 
        for y in range(min_y, max_y + 1):
            intersections_x = []
            # Находим пересечения всех ребер с текущей строкой y
            for edge in edge_table_full:
                # Ребро пересекает строку y, если y_min <= y < y_max
                if edge['y_min'] <= y < edge['y_max']:
                    # Вычисляем x пересечения для текущего y
                    # x = x_at_y_min + slope_inv * (y - y_min)
                    x_intersect = edge['x_at_y_min'] + edge['slope_inv'] * (y - edge['y_min'])
                    intersections_x.append(x_intersect)

            # Сортируем точки пересечения по X
            intersections_x.sort()

            # Заполняем пиксели между парами пересечений
            for i in range(0, len(intersections_x), 2):
                if i + 1 < len(intersections_x):
                    x_start = math.ceil(intersections_x[i])
                    x_end = math.floor(intersections_x[i+1])
                    for x in range(x_start, x_end + 1):
                        self._plot_pixel(canvas, x, y, fill_color, fill_tag)

        return fill_tag


# --- Контекст и Меню ---
class FillContext:
    """Контекст для выбора и выполнения стратегии заливки."""
    def __init__(self):
        self.__strategy: FillStrategyInterface = None
        self.strategies = {
            "Растровая развертка с ET и AEL": ET_AEL_FillStrategy(),
            "Простой алгоритм с затравкой": FloodFillStrategy(),
            "Построчный алгоритм с затравкой": ScanlineSeedFillStrategy(),
            "Сканлайн с ET (простой)": ET_FillStrategy(),
        }
        self.set_strategy("Растровая развертка с ET и AEL")

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
            result = self.__strategy.fill(canvas, polygon_points, fill_color, **kwargs)
            end_time = time.time()
            if isinstance(result, str): # ET+AEL возвращает тег
                 print(f"Стратегия '{self.__strategy.name}' завершена за {end_time - start_time:.4f} сек. Тег: {result}")
                 return result # Возвращаем тег
            elif Image is not None and isinstance(result, Image.Image): # Flood/Scanline возвращают Image
                 print(f"Стратегия '{self.__strategy.name}' завершена за {end_time - start_time:.4f} сек.")
                 return result # Возвращаем измененное изображение PIL
            else: # Ошибка или Pillow не установлен
                 print(f"Стратегия '{self.__strategy.name}' не выполнена или вернула некорректный результат.")
                 return None

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
        strategy = self.context.get_strategy()
        if strategy and strategy.requires_seed:
            print("Активация инструмента для выбора точки затравки...")
            self.activate_tool_callback()
        elif strategy: # Для ET+AEL (не требует затравки)
             print("Активация инструмента заливки (без затравки)...")
             self.activate_tool_callback()


    def show_algorithm_menu(self):
        # Убедимся что кнопка существует перед показом меню
        if self.button and self.button.winfo_exists():
             self.algorithm_menu.post(self.button.winfo_rootx(), self.button.winfo_rooty() + self.button.winfo_height())
        else:
             print("Ошибка: Невозможно показать меню, кнопка не найдена.") 