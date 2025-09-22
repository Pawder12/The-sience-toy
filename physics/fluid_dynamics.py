# physics/fluid_dynamics.py
import numpy as np
from numba import njit, prange

@njit
def compute_pressure_gradient(pressure, h, w):
    """Вычисляет градиент давления (для движения жидкостей)"""
    grad_x = np.zeros((h, w), dtype=np.float32)
    grad_y = np.zeros((h, w), dtype=np.float32)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            grad_x[y, x] = (pressure[y, x+1] - pressure[y, x-1]) * 0.5
            grad_y[y, x] = (pressure[y+1, x] - pressure[y-1, x]) * 0.5
    return grad_x, grad_y

@njit
def update_velocity_from_pressure(vx, vy, pressure_grad_x, pressure_grad_y, density, dt=0.1):
    """Обновляет скорость под действием давления: F = -∇P"""
    for y in range(vx.shape[0]):
        for x in range(vx.shape[1]):
            if density[y, x] > 0:
                vx[y, x] -= dt * pressure_grad_x[y, x] / density[y, x]
                vy[y, x] -= dt * pressure_grad_y[y, x] / density[y, x]

@njit
def diffuse_field(field, new_field, diffusivity, dt, h, w):
    """Диффузия поля (давление, температура, радиация)"""
    alpha = diffusivity * dt
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            center = field[y, x]
            neighbors = (
                field[y+1,x] + field[y-1,x] +
                field[y,x+1] + field[y,x-1]
            ) / 4.0
            new_field[y, x] = center + alpha * (neighbors - center)

@njit
def advect_field(field, vx, vy, dt, h, w):
    """Адвекция: перенос поля по скорости (semi-Lagrangian)"""
    new_field = np.copy(field)
    for y in range(h):
        for x in range(w):
            dx = vx[y, x] * dt
            dy = vy[y, x] * dt
            x_prev = x - dx
            y_prev = y - dy
            x_prev = max(0, min(w - 1, x_prev))
            y_prev = max(0, min(h - 1, y_prev))
            i0, j0 = int(x_prev), int(y_prev)
            i1, j1 = min(i0 + 1, w - 1), min(j0 + 1, h - 1)
            fx = x_prev - i0
            fy = y_prev - j0
            value = (
                field[j0, i0] * (1 - fx) * (1 - fy) +
                field[j0, i1] * fx * (1 - fy) +
                field[j1, i0] * (1 - fx) * fy +
                field[j1, i1] * fx * fy
            )
            new_field[y, x] = value
    return new_field

@njit
def compute_vorticity(vx, vy, h, w):
    """Вычисляет завихренность ω = ∂vy/∂x - ∂vx/∂y"""
    vort = np.zeros((h, w), dtype=np.float32)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            dvx_dy = (vx[y+1,x] - vx[y-1,x]) * 0.5
            dvy_dx = (vy[y,x+1] - vy[y,x-1]) * 0.5
            vort[y, x] = dvy_dx - dvx_dy
    return vort

@njit
def apply_vortex_force(vx, vy, vort, strength=0.1):
    """Добавляет силу от вихря (турбулентность)"""
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if abs(vort[y, x]) > 0.5:
                noise = np.random.rand() * strength
                vx[y, x] += noise
                vy[y, x] += noise

@njit(parallel=True)
def step_fluid(
    grid_type, pressure, vx, vy, density,
    dt=0.1, viscosity=0.1, h=600, w=600
):
    """Полный шаг гидродинамики: диффузия, адвекция, давление"""
    # Сохраняем текущие скорости
    vx_old = np.copy(vx)
    vy_old = np.copy(vy)

    # Диффузия скорости (вязкость)
    diffuse_field(vx_old, vx, viscosity, dt, h, w)
    diffuse_field(vy_old, vy, viscosity, dt, h, w)

    # Адвекция скорости
    vx[:] = advect_field(vx, vx_old, vy_old, dt, h, w)
    vy[:] = advect_field(vy, vx_old, vy_old, dt, h, w)

    # Обновляем давление
    pressure_new = np.zeros_like(pressure)
    diffuse_field(pressure, pressure_new, 1.0, dt, h, w)
    pressure[:] = pressure_new

    # Градиент давления → движение
    px, py = compute_pressure_gradient(pressure, h, w)
    update_velocity_from_pressure(vx, vy, px, py, density, dt)

    # Вихревая коррекция (турбулентность)
    vort = compute_vorticity(vx, vy, h, w)
    apply_vortex_force(vx, vy, vort, strength=0.05)