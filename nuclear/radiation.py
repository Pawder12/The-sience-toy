# nuclear/radiation.py
import numpy as np
from numba import njit, prange

# Типы излучения
ALPHA = 1
BETA = 2
GAMMA = 3

# Глубина проникновения (в пикселях)
PENETRATION = {
    ALPHA: 2,
    BETA: 10,
    GAMMA: 50
}

# Ионизирующая способность
IONIZATION = {
    ALPHA: 10,
    BETA: 3,
    GAMMA: 1
}

@njit
def decay_alpha(grid_type, x, y, h, w, daughter_element):
    """Альфа-распад: испускается He-ядро"""
    grid_type[y, x] = daughter_element
    # Альфа-частица движется короткое расстояние
    angle = np.random.rand() * 2 * np.pi
    for i in range(PENETRATION[ALPHA]):
        nx = x + int(i * np.cos(angle))
        ny = y + int(i * np.sin(angle))
        if 0 <= nx < w and 0 <= ny < h:
            pass  # просто ионизирует среду
    return 4.5  # MeV

@njit
def decay_beta(grid_type, x, y, h, w, daughter_element):
    """Бета-распад: электрон вылетает"""
    grid_type[y, x] = daughter_element
    angle = np.random.rand() * 2 * np.pi
    for i in range(PENETRATION[BETA]):
        nx = x + int(i * np.cos(angle) * np.random.rand())
        ny = y + int(i * np.sin(angle) * np.random.rand())
        if 0 <= nx < w and 0 <= ny < h:
            if grid_type[ny, nx] == 104:  # RBC
                if np.random.rand() < 0.1:
                    grid_type[ny, nx] = 106  # мутирует в раковую
    return 0.5  # MeV

@njit
def emit_gamma(grid_radiation, x, y, energy_mev):
    """Гамма-излучение распространяется далеко"""
    radius = int(energy_mev * 10)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                dist = max(np.sqrt(dx*dx + dy*dy), 1.0)
                intensity = energy_mev / (dist * dist)
                grid_radiation[ny, nx] += intensity * 10

@njit
def irradiate_cell(grid_type, damage_map, x, y, dose):
    """Наносит повреждение клетке"""
    if grid_type[y, x] in [100, 101, 102, 103, 104]:
        damage_map[y, x] += dose
        if damage_map[y, x] > DAMAGE_THRESHOLD:
            grid_type[y, x] = 0  # клетка умирает

@njit
def check_natural_decay(grid_type, grid_half_life, grid_age, x, y):
    """Проверяет, произошёл ли распад по времени"""
    if grid_half_life[y, x] <= 0:
        return False
    probability = 1 - np.exp(-np.log(2) / grid_half_life[y, x])
    return np.random.rand() < probability

@njit(parallel=True)
def step_radiation(
    grid_type, grid_radiation, grid_damage,
    grid_half_life, grid_age, h, w
):
    """
    Главный шаг радиации: распад, излучение, повреждение
    """
    for idx in prange(h * w):
        y = idx // w
        x = idx % w
        elem = grid_type[y, x]
        grid_age[y, x] += 1

        dose = 0.0

        if elem == 60:  # Cs-137
            if check_natural_decay(grid_type, grid_half_life, grid_age, x, y):
                grid_type[y, x] = 61  # → I-131
                dose += decay_beta(grid_type, x, y, h, w, 61)
                emit_gamma(grid_radiation, x, y, 0.662)
        elif elem == 61:  # I-131
            if check_natural_decay(grid_type, grid_half_life, grid_age, x, y):
                grid_type[y, x] = 50  # условно
                dose += decay_beta(grid_type, x, y, h, w, 50)
                emit_gamma(grid_radiation, x, y, 0.364)
        elif elem == 62:  # Sr-90
            if check_natural_decay(grid_type, grid_half_life, grid_age, x, y):
                grid_type[y, x] = 54  # Y-90
                dose += decay_beta(grid_type, x, y, h, w, 54)
        elif elem == 50 or elem == 52:
            dose += 0.1  # фоновое гамма-излучение

        # Распространение радиации
        if dose > 0:
            emit_gamma(grid_radiation, x, y, dose)

        # Затухание радиации
        grid_radiation[y, x] *= 0.995

        # Нанесение повреждений живым клеткам
        if grid_radiation[y, x] > 0.5:
            irradiate_cell(grid_type, grid_damage, x, y, grid_radiation[y, x] * 0.01)