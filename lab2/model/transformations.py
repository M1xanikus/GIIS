import numpy as np
import math

def translate_2d(points, dx, dy):
    """Перемещает все точки на dx, dy."""
    matrix = np.array([
        [1, 0, dx],
        [0, 1, dy],
        [0, 0, 1]
    ])
    new_points = []
    print(f"[DEBUG transform] translate_2d input points: {points}") # Debug input
    for i, p in enumerate(points):
        print(f"[DEBUG transform] Processing point {i}: {p}, type: {type(p)}") # Debug point
        # Ensure p is a valid list/tuple of numbers before creating numpy array
        if not isinstance(p, (list, tuple)) or len(p) != 2:
             print(f"[DEBUG transform] Skipping invalid point structure: {p}")
             continue # Skip this point
        try:
            point_vec = np.array([p[0], p[1], 1], dtype=float) # Ensure float type
            print(f"[DEBUG transform] Point vector: {point_vec}, shape: {point_vec.shape}") # Debug vector
            new_vec = matrix @ point_vec
            new_points.append([new_vec[0], new_vec[1]])
        except Exception as e:
            print(f"[DEBUG transform] Error processing point {p}: {e}")
            # Decide how to handle error: skip point, return original, raise? Let's skip.
            continue
    print(f"[DEBUG transform] translate_2d output points: {new_points}") # Debug output
    return new_points

def rotate_2d(points, angle_degrees, center_x, center_y):
    """Поворачивает точки вокруг центра на заданный угол."""
    angle_rad = math.radians(angle_degrees)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    # Матрица переноса к началу координат, поворота и переноса обратно
    to_origin = np.array([
        [1, 0, -center_x],
        [0, 1, -center_y],
        [0, 0, 1]
    ])
    rotate_matrix = np.array([
        [cos_a, -sin_a, 0],
        [sin_a, cos_a,  0],
        [0,     0,      1]
    ])
    from_origin = np.array([
        [1, 0, center_x],
        [0, 1, center_y],
        [0, 0, 1]
    ])

    # Комбинированная матрица
    matrix = from_origin @ rotate_matrix @ to_origin

    new_points = []
    print(f"[DEBUG transform] rotate_2d input points: {points}, angle: {angle_degrees}, center: ({center_x}, {center_y})")
    for i, p in enumerate(points):
        print(f"[DEBUG transform] Processing point {i}: {p}, type: {type(p)}")
        if not isinstance(p, (list, tuple)) or len(p) != 2:
             print(f"[DEBUG transform] Skipping invalid point structure: {p}")
             continue
        try:
            point_vec = np.array([p[0], p[1], 1], dtype=float)
            new_vec = matrix @ point_vec
            new_points.append([new_vec[0], new_vec[1]])
        except Exception as e:
            print(f"[DEBUG transform] Error processing point {p}: {e}")
            continue
    print(f"[DEBUG transform] rotate_2d output points: {new_points}")
    return new_points

def scale_2d(points, sx, sy, center_x, center_y):
    """Масштабирует точки относительно центра."""
    # Предотвращение нулевого масштаба
    sx = max(sx, 0.01)
    sy = max(sy, 0.01)

    # Матрица переноса к началу координат, масштабирования и переноса обратно
    to_origin = np.array([
        [1, 0, -center_x],
        [0, 1, -center_y],
        [0, 0, 1]
    ])
    scale_matrix = np.array([
        [sx, 0,  0],
        [0,  sy, 0],
        [0,  0,  1]
    ])
    from_origin = np.array([
        [1, 0, center_x],
        [0, 1, center_y],
        [0, 0, 1]
    ])

    # Комбинированная матрица
    matrix = from_origin @ scale_matrix @ to_origin

    new_points = []
    print(f"[DEBUG transform] scale_2d input points: {points}, scale: ({sx}, {sy}), center: ({center_x}, {center_y})")
    for i, p in enumerate(points):
        print(f"[DEBUG transform] Processing point {i}: {p}, type: {type(p)}")
        if not isinstance(p, (list, tuple)) or len(p) != 2:
             print(f"[DEBUG transform] Skipping invalid point structure: {p}")
             continue
        try:
            point_vec = np.array([p[0], p[1], 1], dtype=float)
            new_vec = matrix @ point_vec
            new_points.append([new_vec[0], new_vec[1]])
        except Exception as e:
            print(f"[DEBUG transform] Error processing point {p}: {e}")
            continue
    print(f"[DEBUG transform] scale_2d output points: {new_points}")
    return new_points

def get_center(points):
    """Вычисляет геометрический центр (среднее арифметическое) точек."""
    if not points: return 0, 0
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    count = len(points)
    return sum_x / count, sum_y / count 