# physics/elasticity.py
import numpy as np
from numba import njit, prange

@njit
def young_modulus(elem_id):
    """Модуль Юнга (Па)"""
    values = {
        62: 200e9,   # Steel Spring
        60: 1e7,     # Rubber
        61: 5e6,     # Silicone
        67: 50e6,    # Composite Beam
    }
    return values.get(elem_id, 1e9)

@njit
def damping_ratio(elem_id):
    """Коэффициент демпфирования"""
    values = {
        60: 0.05,
        61: 0.08,
        65: 0.3,
        62: 0.02,
    }
    return values.get(elem_id, 0.1)

@njit
def update_spring_forces(
    grid_type, vx, vy, rest_length_map,
    spring_constant, h, w
):
    """Сила пружины: F = -k * (L - L₀)"""
    force_x = np.zeros((h, w), dtype=np.float32)
    force_y = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            if grid_type[y, x] != 62:  # не пружина
                continue
            # Проверяем соседей (упрощённо)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and grid_type[ny, nx] == 62:
                        dist = np.sqrt(dx*dx + dy*dy)
                        delta = dist - rest_length_map[y, x]
                        f = -spring_constant * delta
                        fx = f * dx / (dist + 1e-6)
                        fy = f * dy / (dist + 1e-6)
                        force_x[y, x] += fx
                        force_y[y, x] += fy
    return force_x, force_y

@njit
def apply_elastic_deformation(
    grid_type, grid_data, vx, vy, x, y, h, w
):
    """Резина: восстанавливающая сила + демпфирование"""
    elem = grid_type[y, x]
    if elem not in [60, 61]:
        return
    k = young_modulus(elem) * 0.001
    damp = damping_ratio(elem)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and grid_type[ny, nx] == elem:
                dist = max(abs(dx) + abs(dy), 1)
                restore = k / dist
                damp_force = damp * (vx[y,x] - vx[ny,nx])
                vx[y,x] -= restore * dx + damp_force
                vy[y,x] -= restore * dy + damp_force

@njit(parallel=True)
def step_elasticity(
    grid_type, vx, vy, grid_data,
    h, w
):
    """Обновление всех упругих материалов"""
    for idx in prange(h * w):
        y = idx // w
        x = idx % w
        elem = grid_type[y, x]
        if elem in [60, 61]:  # Rubber, Silicone
            apply_elastic_deformation(grid_type, grid_data, vx, vy, x, y, h, w)
        elif elem == 62:  # Spring
            fx, fy = update_spring_forces(grid_type, vx, vy, grid_data, 1000.0, h, w)
            vx[y, x] += fx[y, x] * 0.001
            vy[y, x] += fy[y, x] * 0.001
        elif elem == 65:  # Foam
            vx[y, x] *= 0.95  # демпфирование
            vy[y, x] *= 0.95