# electricity.py
import numpy as np
from numba import njit, prange

@njit
def apply_voltage_gradient(grid_charge, conductivity, voltage_map, dt=0.1):
    """Применяет разность потенциалов"""
    for y in range(1, voltage_map.shape[0]-1):
        for x in range(1, voltage_map.shape[1]-1):
            if conductivity[y, x] > 0:
                grad_x = (voltage_map[y,x+1] - voltage_map[y,x-1]) * 0.5
                grad_y = (voltage_map[y+1,x] - voltage_map[y-1,x]) * 0.5
                current_x = conductivity[y, x] * grad_x * dt
                current_y = conductivity[y, x] * grad_y * dt
                grid_charge[y, x] += current_x + current_y

@njit
def update_electron_flow(grid_type, grid_conductivity, grid_charge, x, y, h, w):
    """Электрон движется по проводнику"""
    if grid_conductivity[y, x] == 0:
        return
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                if grid_conductivity[ny, nx] > 0:
                    if np.random.rand() < 0.3:
                        grid_type[ny, nx] = 8  # electron
                        grid_type[y, x] = 0
                    break

@njit
def emit_spark(grid_type, charge, x, y, h, w):
    """Искра при высоком напряжении"""
    if charge[y, x] > 1000 and np.random.rand() < 0.01:
        for _ in range(3):
            dx = np.random.randint(-2, 3)
            dy = np.random.randint(-2, 3)
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                grid_type[ny, nx] = 4  # огонь
                grid_type[y, x] = 8   # электрон

@njit(parallel=True)
def step_electricity(
    grid_type, grid_conductivity, grid_charge,
    voltage_map, h, w
):
    """Обновление электрических процессов"""
    apply_voltage_gradient(grid_charge, grid_conductivity, voltage_map)
    
    for idx in prange(h * w):
        y = idx // w
        x = idx % w
        if grid_type[y, x] == 8:  # Electron
            update_electron_flow(grid_type, grid_conductivity, grid_charge, x, y, h, w)
        if grid_charge[y, x] > 500:
            emit_spark(grid_type, grid_charge, x, y, h, w)