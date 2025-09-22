# physics/thermodynamics.py
import numpy as np
from numba import njit, prange

STEFAN_BOLTZMANN = 5.67e-8  # W/m²K⁴
ABS_ZERO = 0.0
ROOM_TEMP = 298.0

@njit
def thermal_conductivity(elem_id):
    """Теплопроводность материалов (W/m·K)"""
    values = {
        0: 0.026,   # Air
        2: 0.8,     # Sand
        3: 0.6,     # Water
        6: 401.0,   # Copper
        13: 80.0,   # Iron
        60: 0.16,   # Rubber
        61: 0.2,    # Silicone
    }
    return values.get(elem_id, 0.1)

@njit
def emit_thermal_radiation(temp_k, emissivity=0.9):
    """Мощность излучения: P = εσT⁴"""
    return emissivity * STEFAN_BOLTZMANN * (temp_k ** 4)

@njit
def conduct_heat(grid_type, grid_temp, conductivity_map, h, w, dt=0.1):
    """Теплопроводность между соседями"""
    new_temp = np.copy(grid_temp)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            elem_here = grid_type[y, x]
            if elem_here == 0:  # воздух — слабо проводит
                continue
            temp_here = grid_temp[y, x]
            total_transfer = 0.0
            count = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        neighbor_elem = grid_type[ny, nx]
                        if neighbor_elem != 0:
                            cond_here = thermal_conductivity(elem_here)
                            cond_there = thermal_conductivity(neighbor_elem)
                            avg_cond = (cond_here + cond_there) * 0.5
                            delta_t = grid_temp[ny, nx] - temp_here
                            transfer = avg_cond * delta_t * dt
                            total_transfer += transfer
                            count += 1
            if count > 0:
                new_temp[y, x] += total_transfer / count
    return new_temp

@njit
def radiate_energy(grid_temp, grid_emissivity, h, w, dt=1.0):
    """Охлаждение за счёт излучения"""
    for y in range(h):
        for x in range(w):
            emission = emit_thermal_radiation(grid_temp[y, x], grid_emissivity[y, x])
            energy_loss = emission * dt
            temp_loss = energy_loss * 0.001  # условная теплоёмкость
            grid_temp[y, x] = max(ABS_ZERO, grid_temp[y, x] - temp_loss)

@njit
def apply_external_heating(grid_temp, heat_source_map, dt=1.0):
    """Добавление тепла от внешних источников (огонь, реакции)"""
    for y in range(grid_temp.shape[0]):
        for x in range(grid_temp.shape[1]):
            grid_temp[y, x] += heat_source_map[y, x] * dt

@njit(parallel=True)
def step_thermodynamics(
    grid_type, grid_temp, grid_emissivity,
    heat_sources, h, w, dt=0.1
):
    """Полный шаг термодинамики"""
    # Конвекция и теплопроводность
    grid_temp[:] = conduct_heat(grid_type, grid_temp, None, h, w, dt)
    
    # Излучение
    radiate_energy(grid_temp, grid_emissivity, h, w, dt)
    
    # Внешние источники (огонь, ядерные реакции)
    apply_external_heating(grid_temp, heat_sources, dt)