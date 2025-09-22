# simulator.py
"""
The Particle Simulator — Физическое ядро
Объединяет: гравитацию, давление, тепло, химию, электричество, радиацию, биологию
"""

import numpy as np
from numba import njit, prange

# Константы
MEV_TO_KELVIN = 1.16045e7
G = 9.8 * 0.1  # Гравитация (масштабирована под пиксели)
DAMPING = 0.98
MIN_TEMP = 0.1

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (Numba-compatible) ===

@njit
def in_bounds(y, x, h, w):
    return 0 <= y < h and 0 <= x < w

@njit
def randf():
    return np.random.rand()

# === ОСНОВНОЙ ШАГ СИМУЛЯЦИИ ===

@njit(parallel=True)
def step_simulation(
    grid_type,
    grid_temp,
    grid_life,
    grid_vx,
    grid_vy,
    grid_pressure,
    grid_density,
    grid_conductivity,
    grid_charge,
    grid_radiation,
    grid_damage,
    grid_age,
    elements_data,
    reactions_list,
    physics_rules,
    h, w
):
    """
    Единый шаг симуляции — вызывает все физические обновления.
    Выполняется параллельно через numba.prange.
    """
    # Перемешиваем порядок обновления, чтобы избежать артефактов
    indices = create_random_indices(h, w)

    for idx in prange(h * w):
        flat_idx = indices[idx]
        y = flat_idx // w
        x = flat_idx % w

        elem_id = grid_type[y, x]
        if elem_id == 0:
            continue  # Air — ничего не делаем

        element = elements_data.get(elem_id, None)
        if element is None:
            continue

        # === 1. Гравитация (для твёрдых и жидких) ===
        if element["state"] in ("solid", "liquid"):
            if y < h - 1:
                below = grid_type[y + 1, x]
                if below == 0 or elements_data.get(below, {}).get("state") == "liquid":
                    # Падение вниз
                    grid_type[y + 1, x] = elem_id
                    grid_temp[y + 1, x] = grid_temp[y, x]
                    grid_type[y, x] = below
                    grid_temp[y, x] = grid_temp[y + 1, x]

        # === 2. Движение жидкостей (вода, кислота) ===
        if element["state"] == "liquid" and y < h - 1:
            # Вниз
            if grid_type[y + 1, x] == 0:
                grid_type[y + 1, x] = elem_id
                grid_temp[y + 1, x] = grid_temp[y, x]
                grid_type[y, x] = 0
            else:
                # Вбок
                dx = 1 if randf() > 0.5 else -1
                nx = x + dx
                if in_bounds(y, nx, h, w) and grid_type[y, nx] == 0:
                    grid_type[y, nx] = elem_id
                    grid_temp[y, nx] = grid_temp[y, x]
                    grid_type[y, x] = 0

        # === 3. Огонь и дым ===
        if elem_id == 4:  # Fire
            grid_life[y, x] -= 1
            if grid_life[y, x] <= 0:
                grid_type[y, x] = 0
            else:
                # Поднимается вверх
                if y > 0 and grid_type[y - 1, x] in (0, 3, 5):
                    grid_type[y - 1, x] = 4
                    grid_life[y - 1, x] = 30
                    grid_temp[y - 1, x] = max(grid_temp[y - 1, x], 1200)

        elif elem_id == 5:  # Smoke
            if y > 0 and randf() > 0.7 and grid_type[y - 1, x] == 0:
                grid_type[y - 1, x] = 5
                grid_type[y, x] = 0
            else:
                dx = 1 if randf() > 0.5 else -1
                nx = x + dx
                if in_bounds(y, nx, h, w) and grid_type[y, nx] == 0:
                    grid_type[y, nx] = 5
                    grid_type[y, x] = 0

        # === 4. Температура и теплопроводность ===
        temp_change = element.get("temp_change", 0.1)
        heat_cond = element.get("heat_conduct", 0.1)
        if heat_cond > 0:
            avg_temp = 0.0
            count = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if in_bounds(ny, nx, h, w):
                        avg_temp += grid_temp[ny, nx]
                        count += 1
            if count > 0:
                delta = (avg_temp / count - grid_temp[y, x]) * heat_cond * 0.1
                grid_temp[y, x] += delta

        # Охлаждение до окружающей среды
        if grid_temp[y, x] > 298:
            grid_temp[y, x] *= 0.999

        # === 5. Возгорание (если горючий и горячий) ===
        if element.get("flammable", 0) > 0 and grid_temp[y, x] > 500 and randf() < 0.005:
            grid_type[y, x] = 4
            grid_life[y, x] = 30
            grid_temp[y, x] = 1500

        # === 6. Возраст клеток ===
        if element["state"] == "cell":
            grid_age[y, x] += 1
            if grid_age[y, x] > 10000:  # старение
                grid_type[y, x] = 0

        # === 7. Радиоактивность ===
        if element.get("radioactive"):
            if randf() < 1e-5:
                grid_radiation[y, x] += 10
                if randf() < 0.3:
                    grid_type[y, x] = 60  # Cs-137 как продукт

        # === 8. Повреждение от радиации ===
        if grid_radiation[y, x] > 1 and element["state"] == "cell":
            grid_damage[y, x] += grid_radiation[y, x] * 0.01
            if grid_damage[y, x] > 100:
                grid_type[y, x] = 0  # клетка умирает

    # === ЗАВЕРШАЮЩИЕ ШАГИ (после основного цикла) ===

    # Химические реакции
    step_chemistry_numba(
        grid_type, grid_temp, grid_life,
        reactions_list, h, w
    )

    # Электричество
    step_electricity_numba(
        grid_type, grid_conductivity, grid_charge,
        h, w
    )

    # Давление и поток
    step_fluid_dynamics_numba(
        grid_type, grid_pressure, grid_vx, grid_vy, grid_density,
        h, w
    )

    # Ядерные реакции
    step_fission_numba(grid_type, grid_temp, grid_radiation, h, w)
    step_radiation_numba(grid_type, grid_radiation, grid_damage, h, w)


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (внутренние) ===

@njit
def create_random_indices(h, w):
    """Создаёт перемешанный массив индексов"""
    indices = np.arange(h * w)
    for i in range(h * w):
        j = np.random.randint(i, h * w)
        indices[i], indices[j] = indices[j], indices[i]
    return indices


# === МОКИ ДЛЯ МОДУЛЕЙ (можно заменить на настоящие) ===

@njit
def step_chemistry_numba(grid_type, grid_temp, grid_life, reactions, h, w):
    for _ in range(1): pass  # заглушка

@njit
def step_electricity_numba(grid_type, conductivity, charge, h, w):
    for _ in range(1): pass

@njit
def step_fluid_dynamics_numba(grid_type, pressure, vx, vy, density, h, w):
    for _ in range(1): pass

@njit
def step_fission_numba(grid_type, grid_temp, grid_radiation, h, w):
    for _ in range(1): pass

@njit
def step_radiation_numba(grid_type, grid_radiation, grid_damage, h, w):
    for _ in range(1): pass


# === УДОБНЫЙ ИНТЕРФЕЙС (для main.py) ===

def step_simulation_wrapper(grid, elements_data, reactions_list, physics_rules):
    """
    Обёртка для вызова из main.py
    """
    step_simulation(
        grid.type,
        grid.temp,
        grid.life,
        grid.vx,
        grid.vy,
        grid.pressure,
        grid.density,
        grid.conductivity,
        grid.charge,
        grid.radiation,
        grid.damage,
        grid.age,
        elements_data,
        reactions_list,
        physics_rules,
        grid.h, grid.w
    )