# nuclear/fission.py
import numpy as np
from numba import njit, prange

# Константы
MEV_TO_KELVIN = 1.16045e7
NEUTRON_SPEED = 2.2e3  # м/с (тепловые нейтроны)
CRITICAL_MASS_U235_KG = 52
CRITICAL_RADIUS_PX = 8  # при плотности 19.1 г/см³ и разрешении 1px = 1 мм

@njit
def is_critical_mass_nearby(grid_type, x, y, h, w, element_id):
    """
    Проверяет, находится ли делящийся материал в критической конфигурации
    (упрощённо: шар радиусом ~8 пикселей)
    """
    count = 0
    for dy in range(-CRITICAL_RADIUS_PX, CRITICAL_RADIUS_PX + 1):
        for dx in range(-CRITICAL_RADIUS_PX, CRITICAL_RADIUS_PX + 1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                dist_sq = dx*dx + dy*dy
                if dist_sq <= CRITICAL_RADIUS_PX * CRITICAL_RADIUS_PX:
                    if grid_type[ny, nx] == element_id:
                        count += 1
    volume = 4/3 * 3.14159 * (CRITICAL_RADIUS_PX ** 3)
    density_factor = count / volume
    return density_factor > 0.7  # если заполнено >70% — может быть цепная реакция

@njit
def emit_neutrons(grid_type, x, y, count, speed=1):
    """Создаёт нейтроны вокруг точки"""
    for _ in range(int(count)):
        angle = np.random.rand() * 2 * np.pi
        dx = int(np.cos(angle) * speed)
        dy = int(np.sin(angle) * speed)
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h and grid_type[ny, nx] == 0:
            grid_type[ny, nx] = 54  # Thermal Neutron

@njit
def absorb_neutron(grid_type, x, y, absorber_id):
    """Поглощает нейтрон (например, бором или кадмием)"""
    grid_type[y, x] = absorber_id

@njit
def fission_products():
    """Возвращает случайные продукты деления"""
    products = [60, 61, 62]  # Cs-137, I-131, Sr-90
    return np.random.choice(products)

@njit
def update_fissile_material(
    grid_type, grid_temp, grid_radiation,
    x, y, h, w, element_id, neutrons_per_fission=2.4,
    energy_mev=200
):
    """
    Обновляет делящийся материал: может произойти деление
    """
    # Спонтанное деление
    if np.random.rand() < 5e-8:
        energy = energy_mev * MEV_TO_KELVIN
        grid_temp[y, x] += energy * 0.1
        emit_neutrons(grid_type, x, y, neutrons_per_fission)
        grid_radiation[y, x] += 50
        grid_type[y, x] = fission_products()
        return

    # Деление под действием нейтрона
    has_neutron = False
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and grid_type[ny, nx] == 54:
                has_neutron = True
                grid_type[ny, nx] = 0  # нейтрон поглощён
                break
        if has_neutron:
            break

    if has_neutron:
        energy = energy_mev * MEV_TO_KELVIN
        grid_temp[y, x] += energy
        emit_neutrons(grid_type, x, y, neutrons_per_fission)
        grid_radiation[y, x] += 100
        # Частичное превращение в продукты деления
        if np.random.rand() < 0.05:
            grid_type[y, x] = fission_products()

@njit(parallel=True)
def step_fission(
    grid_type, grid_temp, grid_radiation,
    h, w
):
    """
    Главный шаг деления: проверка всех ячеек на возможное деление
    """
    for idx in prange(h * w):
        y = idx // w
        x = idx % w
        elem = grid_type[y, x]

        if elem == 50:  # Uranium-235
            update_fissile_material(
                grid_type, grid_temp, grid_radiation,
                x, y, h, w, 50, neutrons_per_fission=2.4, energy_mev=200
            )
        elif elem == 52:  # Plutonium-239
            update_fissile_material(
                grid_type, grid_temp, grid_radiation,
                x, y, h, w, 52, neutrons_per_fission=2.89, energy_mev=210
            )
        elif elem == 53:  # Pu-240 — спонтанное деление
            if np.random.rand() < 1e-5:
                emit_neutrons(grid_type, x, y, 3, speed=2)
                grid_temp[y, x] += 50 * MEV_TO_KELVIN