  # model/polygon_analysis.py
import math

def _orientation(p, q, r):
    """Определяет ориентацию упорядоченного триплета (p, q, r).
    Возвращает:
    0 --> p, q, r коллинеарны
    1 --> По часовой стрелке
    2 --> Против часовой стрелки
    """
    val = (q[1] - p[1]) * (r[0] - q[0]) - \
          (q[0] - p[0]) * (r[1] - q[1])
    if val == 0: return 0  # Коллинеарны
    return 1 if val > 0 else 2  # По часовой или против часовой

def is_convex(points):
    """Проверяет, является ли полигон, заданный точками, выпуклым.
    Предполагается, что точки даны в порядке обхода (по часовой или против).
    """
    n = len(points)
    if n < 3:
        return False # Не полигон

    # Находим ориентацию для первого валидного триплета
    first_orientation = None
    for i in range(n):
        o = _orientation(points[i], points[(i + 1) % n], points[(i + 2) % n])
        if o != 0: # Нашли не коллинеарный триплет
            first_orientation = o
            break

    # Если все точки коллинеарны, формально не выпуклый (или вырожденный)
    if first_orientation is None:
        return False

    # Проверяем, что все остальные повороты имеют ту же ориентацию (или коллинеарны)
    for i in range(n):
        o = _orientation(points[i], points[(i + 1) % n], points[(i + 2) % n])
        if o != 0 and o != first_orientation:
            return False # Нашли поворот в другую сторону

    return True

def get_inner_normals(points):
    """Вычисляет внутренние нормали для выпуклого полигона.
    Предполагается, что точки даны в порядке обхода ПРОТИВ часовой стрелки.
    Возвращает список пар: (середина_ребра, вектор_нормали).
    """
    n = len(points)
    if n < 3:
        return []

    # Проверяем (или предполагаем) выпуклость и обход против часовой
    # Для простоты здесь предполагаем, что полигон выпуклый и CCW
    # Проверка на CCW:
    # Найдем самую нижнюю (потом самую левую) точку
    min_y_idx = 0
    for i in range(1, n):
        if points[i][1] < points[min_y_idx][1] or \
           (points[i][1] == points[min_y_idx][1] and points[i][0] < points[min_y_idx][0]):
            min_y_idx = i
    # Проверим ориентацию относительно этой точки
    prev_idx = (min_y_idx - 1 + n) % n
    next_idx = (min_y_idx + 1) % n
    if _orientation(points[prev_idx], points[min_y_idx], points[next_idx]) == 1: # По часовой
        print("Warning: Polygon might be clockwise. Reversing points for inner normals.")
        points = points[::-1] # Разворачиваем для CCW

    normals = []
    for i in range(n):
        p1 = points[i]
        p2 = points[(i + 1) % n]

        # Вектор ребра
        edge_vec = (p2[0] - p1[0], p2[1] - p1[1])

        # Нормаль (поворот на 90 градусов влево для CCW)
        # dx, dy -> -dy, dx
        normal_vec = (-edge_vec[1], edge_vec[0])

        # Нормализуем вектор нормали (опционально, но полезно)
        length = math.sqrt(normal_vec[0]**2 + normal_vec[1]**2)
        if length > 1e-9: # Избегаем деления на ноль
            normal_vec = (normal_vec[0] / length, normal_vec[1] / length)
        else:
            normal_vec = (0, 0) # Для вырожденных случаев

        # Середина ребра для точки приложения нормали
        mid_point = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

        normals.append((mid_point, normal_vec))

    return normals

# --- Функции для пересечения отрезка и полигона ---

def _on_segment(p, q, r):
    """Проверяет, лежит ли точка q на отрезке pr."""
    return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
            q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))

def intersect_segment_edge(p1, q1, p2, q2):
    """Находит точку пересечения отрезков p1q1 и p2q2, если она есть."""
    o1 = _orientation(p1, q1, p2)
    o2 = _orientation(p1, q1, q2)
    o3 = _orientation(p2, q2, p1)
    o4 = _orientation(p2, q2, q1)

    # Общий случай пересечения
    if o1 != o2 and o3 != o4:
        # Находим точку пересечения линий
        x1, y1 = p1
        x2, y2 = q1
        x3, y3 = p2
        x4, y4 = q2
        denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denominator) < 1e-9: # Линии почти параллельны
             return None
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denominator
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denominator

        # Проверяем, что точка пересечения лежит на обоих отрезках (с небольшой погрешностью)
        eps = 1e-9
        if -eps <= t <= 1 + eps and -eps <= u <= 1 + eps:
            intersection_x = x1 + t * (x2 - x1)
            intersection_y = y1 + t * (y2 - y1)
            return (intersection_x, intersection_y)
        else:
            return None # Пересечение линий вне отрезков

    # Специальные случаи (коллинеарность) - пока не обрабатываем перекрытие
    # Вернем точку, если один конец одного отрезка лежит на другом.
    if o1 == 0 and _on_segment(p1, p2, q1): return p2
    if o2 == 0 and _on_segment(p1, q2, q1): return q2
    if o3 == 0 and _on_segment(p2, p1, q2): return p1
    if o4 == 0 and _on_segment(p2, q1, q2): return q1

    return None # Отрезки не пересекаются

def segment_intersects_polygon(segment_start, segment_end, polygon_points):
    """Находит все точки пересечения отрезка с ребрами полигона."""
    n = len(polygon_points)
    if n < 3: return []

    intersection_points = []
    p1 = segment_start
    q1 = segment_end

    for i in range(n):
        p2 = polygon_points[i]
        q2 = polygon_points[(i + 1) % n] # Следующая вершина полигона
        intersection = intersect_segment_edge(p1, q1, p2, q2)
        if intersection:
            # Проверяем на дубликаты (может возникнуть при пересечении в вершине)
            is_duplicate = False
            for existing_point in intersection_points:
                if math.isclose(intersection[0], existing_point[0], abs_tol=1e-6) and \
                   math.isclose(intersection[1], existing_point[1], abs_tol=1e-6):
                    is_duplicate = True
                    break
            if not is_duplicate:
                intersection_points.append(intersection)

    return intersection_points

# --- Функция для принадлежности точки полигону ---

def point_in_polygon(point, polygon_points):
    """Проверяет принадлежность точки полигону с помощью алгоритма трассировки луча.
    Возвращает:
        "inside" - точка строго внутри
        "outside" - точка строго снаружи
        "boundary" - точка на границе
    """
    n = len(polygon_points)
    if n < 3: return "outside"

    x, y = point
    on_boundary = False
    for i in range(n):
        p1 = polygon_points[i]
        p2 = polygon_points[(i + 1) % n]
        if _orientation(p1, p2, point) == 0 and _on_segment(p1, point, p2):
            on_boundary = True
            break
    if on_boundary:
        return "boundary"

    # Алгоритм четности-нечетности (Ray Casting)
    inside = False
    for i in range(n):
        p1 = polygon_points[i]
        p2 = polygon_points[(i + 1) % n]
        x1, y1 = p1
        x2, y2 = p2

        # Проверяем пересечение горизонтального луча вправо с ребром (p1, p2)
        if ((y1 <= y < y2) or (y2 <= y < y1)) and \
           (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
            inside = not inside

    return "inside" if inside else "outside" 