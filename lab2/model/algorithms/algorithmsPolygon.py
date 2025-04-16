from abc import ABC, abstractmethod
import math
import time
from functools import cmp_to_key
import tkinter as tk # Нужен импорт tk для меню

class PolygonStrategyInterface(ABC):
    """Интерфейс для алгоритмов построения выпуклой оболочки."""
    @abstractmethod
    def __init__(self):
        self.name = None

    @abstractmethod
    def execute(self, points, canvas):
        """
        Выполняет алгоритм построения выпуклой оболочки.

        Args:
            points (list[tuple[int, int]]): Список исходных точек (x, y).
            canvas (tk.Canvas): Холст для отрисовки результата.

        Returns:
            tuple[str, list[tuple[int, int]]]: Кортеж с тегом фигуры и списком точек оболочки.
        """
        pass

def _orientation(p, q, r):
    """
    Определяет ориентацию упорядоченного триплета (p, q, r).
    Возвращает:
     0 --> p, q и r коллинеарны
     1 --> По часовой стрелке
     2 --> Против часовой стрелки
    """
    val = ((q[1] - p[1]) * (r[0] - q[0]) -
           (q[0] - p[0]) * (r[1] - q[1]))
    if val == 0: return 0  # Коллинеарны
    return 1 if val > 0 else 2 # По часовой или против часовой

def _dist_sq(p1, p2):
    """Вычисляет квадрат расстояния между двумя точками."""
    return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2

class JarvisStrategy(PolygonStrategyInterface):
    """Реализация алгоритма Джарвиса (Gift Wrapping)."""
    def __init__(self):
        self.name = "Джарвис"

    def execute(self, points, canvas):
        shape_tag = f"hull_jarvis_{time.time_ns()}"
        n = len(points)
        if n < 3:
            print("Недостаточно точек для построения оболочки (< 3)")
            return shape_tag, [] # Нельзя построить оболочку

        hull = []

        # Находим самую левую точку (или самую нижнюю из левых)
        l = 0
        for i in range(1, n):
            if points[i][0] < points[l][0]:
                l = i
            elif points[i][0] == points[l][0] and points[i][1] < points[l][1]:
                l = i

        p = l
        q = -1 # Инициализация индекса следующей точки
        while True:
            hull.append(points[p])

            # Ищем точку 'q' такую, что триплет (p, q, x) имеет
            # ориентацию против часовой стрелки для всех точек 'x'.
            q = (p + 1) % n # Начинаем со следующей точки

            for i in range(n):
                # Если i-ая точка более "против часовой стрелки", чем текущая q
                orient = _orientation(points[p], points[i], points[q])
                if orient == 2:
                    q = i
                # Если коллинеарны, берем самую дальнюю
                elif orient == 0 and _dist_sq(points[p], points[i]) > _dist_sq(points[p], points[q]):
                    q = i

            p = q

            # Если вернулись к стартовой точке
            if p == l:
                break

        # Отрисовка оболочки на холсте
        if canvas and hull:
            # Преобразуем в формат, ожидаемый create_polygon
            flat_hull = [coord for point in hull for coord in point]
            canvas.create_polygon(flat_hull, outline='red', fill='', width=2, tags=(shape_tag, "hull"))

        return shape_tag, hull


# --- Вспомогательные функции для Грэхема ---
_graham_anchor_point = None # Глобальная (для модуля) опорная точка для сортировки

def _compare_graham(p1, p2):
    """Компаратор для сортировки точек по полярному углу относительно _graham_anchor_point."""
    global _graham_anchor_point
    o = _orientation(_graham_anchor_point, p1, p2)
    if o == 0: # Коллинеарны
        # Точка ближе к опорной идет первой
        return -1 if _dist_sq(_graham_anchor_point, p1) < _dist_sq(_graham_anchor_point, p2) else 1
    # Точка с меньшим углом (более "против часовой") идет первой
    return -1 if o == 2 else 1

class GrahamStrategy(PolygonStrategyInterface):
    """Реализация алгоритма сканирования Грэхема."""
    def __init__(self):
        self.name = "Грэхем"

    def execute(self, points, canvas):
        global _graham_anchor_point
        shape_tag = f"hull_graham_{time.time_ns()}"
        n = len(points)
        if n < 3:
            print("Недостаточно точек для построения оболочки (< 3)")
            return shape_tag, []

        # 1. Найти опорную точку (самую нижнюю, затем самую левую)
        min_y = points[0][1]
        min_idx = 0
        for i in range(1, n):
            y = points[i][1]
            if (y < min_y) or (min_y == y and points[i][0] < points[min_idx][0]):
                min_y = y
                min_idx = i

        # Поменять местами опорную точку с первой точкой
        points[0], points[min_idx] = points[min_idx], points[0]
        _graham_anchor_point = points[0]

        # 2. Отсортировать остальные точки по полярному углу относительно опорной
        # Используем functools.cmp_to_key для адаптации старого компаратора
        sorted_points = sorted(points[1:], key=cmp_to_key(_compare_graham))

        # 3. Обработать коллинеарные точки (оставить самую дальнюю)
        # (Этот шаг часто включен в сортировку или основной цикл)
        # Можно добавить проверку в цикле сканирования.
        processed_points = [_graham_anchor_point]
        for p in sorted_points:
             # Пропускаем точки, слишком близкие к опорной (если необходимо)
             # if _dist_sq(_graham_anchor_point, p) == 0: continue

             # Удаляем точки, коллинеарные с предыдущей и опорной, если они ближе
             while len(processed_points) > 1 and \
                   _orientation(_graham_anchor_point, processed_points[-1], p) == 0:
                 processed_points.pop() # Удаляем последнюю добавленную коллинеарную
             processed_points.append(p)

        if len(processed_points) < 3:
             print("Недостаточно точек после обработки коллинеарных")
             return shape_tag, [] # Все точки коллинеарны

        # 4. Построение оболочки (сканирование)
        hull_stack = [processed_points[0], processed_points[1], processed_points[2]]

        # --- Визуализация: Начальное состояние стека ---
        if canvas:
            debug_tag = f"debug_graham_{shape_tag}"
            flat_stack = [coord for point in hull_stack for coord in point]
            if len(flat_stack) >= 4:
                canvas.create_line(flat_stack, fill='gray', width=1, tags=(debug_tag, "debug_line"))
            for i, p in enumerate(hull_stack):
                 canvas.create_oval(p[0]-2, p[1]-2, p[0]+2, p[1]+2, fill='gray', outline='gray', tags=(debug_tag, "debug_point"))
            canvas.update()
            time.sleep(0.5) # Пауза для наблюдения
        # -------------------------------------------

        for i in range(3, len(processed_points)):
            next_point = processed_points[i]

            # --- Визуализация: Следующая точка и проверка ---
            if canvas:
                 canvas.create_oval(next_point[0]-3, next_point[1]-3, next_point[0]+3, next_point[1]+3,
                                   fill='orange', outline='orange', tags=(debug_tag, "debug_next_point"))
                 if len(hull_stack) >= 2:
                     canvas.create_line(hull_stack[-1][0], hull_stack[-1][1], next_point[0], next_point[1],
                                        fill='orange', width=1, dash=(2, 2), tags=(debug_tag, "debug_check_line"))
                 canvas.update()
                 time.sleep(0.3)
            # ---------------------------------------------

            # Пока поворот не "влево" (против часовой), удаляем вершину стека
            while len(hull_stack) > 1 and _orientation(hull_stack[-2], hull_stack[-1], next_point) != 2:
                 # --- Визуализация: Удаление точки ---
                 if canvas:
                     popped_point = hull_stack[-1]
                     canvas.create_oval(popped_point[0]-4, popped_point[1]-4, popped_point[0]+4, popped_point[1]+4,
                                        fill='', outline='red', width=2, tags=(debug_tag, "debug_pop_indicator"))
                     # Удаляем последнюю линию стека (серую)
                     canvas.delete("debug_line") # Удаляем все серые линии
                     # Перерисовываем стек без последней линии
                     flat_stack_before_pop = [coord for point in hull_stack[:-1] for coord in point]
                     if len(flat_stack_before_pop) >= 4:
                          canvas.create_line(flat_stack_before_pop, fill='gray', width=1, tags=(debug_tag, "debug_line"))

                     canvas.update()
                     time.sleep(0.4)
                     # Удаляем красный индикатор удаления
                     canvas.delete("debug_pop_indicator")
                 # ------------------------------------
                 hull_stack.pop()

            hull_stack.append(next_point)

            # --- Визуализация: Обновленное состояние стека ---
            if canvas:
                 canvas.delete("debug_line") # Удаляем старые линии стека
                 canvas.delete("debug_point") # Удаляем старые точки стека
                 canvas.delete("debug_next_point") # Удаляем оранжевую точку
                 canvas.delete("debug_check_line") # Удаляем оранжевую пунктирную линию

                 flat_stack = [coord for point in hull_stack for coord in point]
                 if len(flat_stack) >= 4:
                     canvas.create_line(flat_stack, fill='blue', width=1, tags=(debug_tag, "debug_line")) # Синяя линия текущего стека
                 for p_idx, p in enumerate(hull_stack):
                     color = 'blue' if p_idx < len(hull_stack) -1 else 'green' # Последняя добавленная - зеленая
                     canvas.create_oval(p[0]-2, p[1]-2, p[0]+2, p[1]+2, fill=color, outline=color, tags=(debug_tag, "debug_point"))

                 canvas.update()
                 time.sleep(0.2)
            # --------------------------------------------

        # Сброс глобальной переменной
        _graham_anchor_point = None

        # --- Очистка визуализации ---
        if canvas:
            canvas.delete(debug_tag)
            canvas.update()
        # --------------------------

        # Отрисовка финальной оболочки на холсте
        if canvas and hull_stack:
            flat_hull = [coord for point in hull_stack for coord in point]
            canvas.create_polygon(flat_hull, outline='blue', fill='', width=2, tags=(shape_tag, "hull"))

        return shape_tag, hull_stack


class PolygonContext:
    """Контекст для выбора и выполнения стратегии построения полигона."""
    def __init__(self):
        self.__strategy: PolygonStrategyInterface = None
        self.strategies = {
            "Джарвис": JarvisStrategy(),
            "Грэхем": GrahamStrategy()
        }
        # Устанавливаем стратегию по умолчанию
        self.set_strategy("Джарвис")

    def set_strategy(self, strategy_name: str):
        if strategy_name in self.strategies:
            self.__strategy = self.strategies[strategy_name]
            print(f"Выбрана стратегия полигонов: {strategy_name}")
        else:
            print(f"Ошибка: Стратегия полигонов '{strategy_name}' не найдена.")

    def get_strategy(self) -> PolygonStrategyInterface:
        return self.__strategy

    def get_available_strategies(self) -> list[str]:
        return list(self.strategies.keys())

    def execute_strategy(self, points, canvas):
        if self.__strategy:
            print(f"Запуск стратегии '{self.__strategy.name}' с {len(points)} точками.")
            start_time = time.time()
            tag, hull_points = self.__strategy.execute(points, canvas)
            end_time = time.time()
            print(f"Стратегия '{self.__strategy.name}' завершена за {end_time - start_time:.4f} сек. Найдено {len(hull_points)} точек оболочки.")
            return tag, hull_points
        else:
            print("Ошибка: Стратегия полигонов не установлена.")
            return None, []

# --- Меню для выбора стратегии ---
class PolygonMenuClass:
    """Класс для создания меню выбора алгоритмов построения выпуклой оболочки."""
    def __init__(self, root, button, context: PolygonContext, activate_tool_callback):
        self.root = root
        self.button = button
        self.context = context
        self.activate_tool_callback = activate_tool_callback
        self.algorithm_menu = tk.Menu(self.root, tearoff=0)

        available_strategies = self.context.get_available_strategies()
        for algo_name in available_strategies:
            self.algorithm_menu.add_command(
                label=algo_name,
                command=lambda name=algo_name: self.select_algorithm(name)
            )

        # Устанавливаем активный алгоритм в меню (если есть)
        current_strategy = self.context.get_strategy()
        if current_strategy:
             # Меню Tkinter не имеет прямого способа "отметить" выбранный пункт
             # Мы просто устанавливаем его в контексте
             pass # select_algorithm уже вызывается при инициализации контекста

    def select_algorithm(self, name):
        print(f"Выбран алгоритм полигонов: {name}")
        self.context.set_strategy(name)
        self.activate_tool_callback() # Активируем инструмент полигонов

    def show_algorithm_menu(self):
        # Отображаем меню рядом с кнопкой
        self.algorithm_menu.post(self.button.winfo_rootx(), self.button.winfo_rooty() + self.button.winfo_height()) 