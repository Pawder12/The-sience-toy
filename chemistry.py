# chemistry.py
import numpy as np
from numba import njit, prange

MEV_TO_KELVIN = 1.16045e7

@njit
def check_reactions_at_point(
    grid_type, grid_temp, grid_life, reactions,
    x, y, h, w
):
    """Проверяет возможные реакции в точке (x,y)"""
    elem = grid_type[y, x]
    temp = grid_temp[y, x]
    
    for rxn in reactions:
        if elem not in rxn['reactants']:
            continue
            
        # Условия
        if 'temp_min' in rxn and temp < rxn['temp_min']:
            continue
        if 'on_contact' not in rxn and np.random.rand() > rxn.get('chance', 1.0):
            continue
            
        # Поиск соседа-реагента
        reacted = False
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    neighbor = grid_type[ny, nx]
                    if neighbor in rxn['reactants'] and np.random.rand() < rxn.get('chance', 1.0):
                        # Реакция!
                        for prod in rxn['products']:
                            grid_type[ny, nx] = prod
                        energy = rxn.get('energy_release', 0)
                        if energy > 0:
                            grid_temp[ny, nx] += energy * MEV_TO_KELVIN * 1e-6
                        if rxn.get('explosion'):
                            create_explosion(grid_type, grid_temp, nx, ny, rxn.get('explosive_power', 1))
                        reacted = True
                        break
            if reacted:
                break

@njit
def create_explosion(grid_type, grid_temp, cx, cy, power):
    """Создаёт взрыв"""
    radius = int(power * 3)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < grid_type.shape[1] and 0 <= ny < grid_type.shape[0]:
                dist_sq = dx*dx + dy*dy
                if dist_sq <= radius * radius:
                    grid_temp[ny, nx] += 1000 * (1 - dist_sq/(radius*radius))
                    if np.random.rand() < 0.3:
                        grid_type[ny, nx] = 5  # smoke
                    if grid_type[ny, nx] == 2:  # sand → glass
                        if np.random.rand() < 0.2:
                            grid_type[ny, nx] = 63  # Glass

@njit
def burn_fuel(grid_type, grid_temp, x, y, fuel_id, oxidizer_id, flame_product, energy):
    """Горение топлива"""
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < grid_type.shape[1] and 0 <= ny < grid_type.shape[0]:
                if grid_type[ny, nx] == oxidizer_id:
                    grid_type[ny, nx] = flame_product
                    grid_temp[ny, nx] += energy
                    grid_type[y, x] = flame_product
                    grid_temp[y, x] += energy
                    return True
    return False

@njit(parallel=True)
def step_chemistry(
    grid_type, grid_temp, grid_life,
    reactions, h, w
):
    """Главный шаг химии"""
    indices = np.random.permutation(h * w)
    for idx in prange(h * w):
        flat_idx = indices[idx]
        y, x = flat_idx // w, flat_idx % w
        elem = grid_type[y, x]
        if elem == 0:
            continue
        check_reactions_at_point(grid_type, grid_temp, grid_life, reactions, x, y, h, w)
        
        # Горение водорода
        if elem == 10 and grid_temp[y, x] > 500:  # H2
            if burn_fuel(grid_type, grid_temp, x, y, 10, 11, 4, 1000):
                pass  # H2 + O2 → огонь
        
        # Разложение кислоты
        if elem == 15 and grid_temp[y, x] > 400:
            grid_type[y, x] = 5  # дым
            grid_temp[y, x] += 200