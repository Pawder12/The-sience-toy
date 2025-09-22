# bio/evolution.py
import numpy as np
from numba import njit, prange
import random

# Глобальные константы
MAX_GENOME_LENGTH = 100
MUTATION_POINT_RATE = 0.002
MUTATION_INSERTION_RATE = 0.0001
MUTATION_DELETION_RATE = 0.0001
RECOMBINATION_RATE = 0.01

# Гены (примеры)
GENES = {
    "OCT4": {"locus": "A1", "function": "pluripotency"},
    "MYOD": {"locus": "B2", "function": "myogenesis"},
    "NEUROD": {"locus": "C3", "function": "neurogenesis"},
    "P53": {"locus": "D4", "function": "tumor_suppression", "apoptosis_trigger": True},
    "HBB": {"locus": "E5", "function": "hemoglobin_beta_chain"},
    "CFTR": {"locus": "F6", "function": "ion_channel"},
    "INS": {"locus": "G7", "function": "insulin_production"}
}

# Признаки и их генетическая основа
TRAITS = {
    "metabolism_rate": {"genes": ["INS"], "base_value": 1.0},
    "radiation_resistance": {"genes": ["P53"], "base_value": 0.3},
    "division_speed": {"genes": ["OCT4"], "base_value": 0.8},
    "muscle_strength": {"genes": ["MYOD"], "base_value": 0.5},
    "neural_connectivity": {"genes": ["NEUROD"], "base_value": 0.6}
}

@njit
def generate_random_dna(length: int = 50) -> str:
    """Создаёт случайную ДНК последовательность"""
    bases = "ACGT"
    return ''.join([bases[np.random.randint(0, 4)] for _ in range(length)])

@njit
def mutate_point(dna: str) -> str:
    """Точечная мутация: A ↔ T, C ↔ G"""
    if len(dna) == 0 or np.random.rand() > MUTATION_POINT_RATE * len(dna):
        return dna
    idx = np.random.randint(0, len(dna))
    base = dna[idx]
    new_base = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}.get(base, 'A')
    return dna[:idx] + new_base + dna[idx+1:]

@njit
def mutate_insertion(dna: str) -> str:
    """Вставка одного нуклеотида"""
    if len(dna) >= MAX_GENOME_LENGTH or np.random.rand() > MUTATION_INSERTION_RATE:
        return dna
    idx = np.random.randint(0, len(dna) + 1)
    new_base = "ACGT"[np.random.randint(0, 4)]
    return dna[:idx] + new_base + dna[idx:]

@njit
def mutate_deletion(dna: str) -> str:
    """Удаление одного нуклеотида"""
    if len(dna) <= 10 or np.random.rand() > MUTATION_DELETION_RATE * len(dna):
        return dna
    idx = np.random.randint(0, len(dna))
    return dna[:idx] + dna[idx+1:]

@njit
def recombine(dna1: str, dna2: str) -> str:
    """Кроссинговер между двумя ДНК"""
    if np.random.rand() > RECOMBINATION_RATE:
        return dna1
    if len(dna1) < 2 or len(dna2) < 2:
        return dna1
    cut1 = np.random.randint(1, len(dna1) - 1)
    cut2 = np.random.randint(1, len(dna2) - 1)
    length = min(cut1, len(dna2) - cut2)
    if length <= 0:
        return dna1
    return dna1[:cut1] + dna2[cut2:cut2 + length] + dna1[cut1 + length:]

@njit
def calculate_trait_value(dna: str, trait_name: str) -> float:
    """Вычисляет фенотипический признак на основе ДНК"""
    trait = TRAITS.get(trait_name)
    if not trait:
        return 0.5
    value = trait["base_value"]
    for gene_name in trait["genes"]:
        gene = GENES.get(gene_name)
        if gene and gene["locus"] in dna:
            value *= 1.5  # усиление при наличии гена
    # Шум мутаций
    value *= (1.0 + np.random.randn() * 0.1)
    return max(0.1, min(value, 5.0))

@njit
def assess_fitness(
    dna: str, temp: float, radiation: float, glucose: float,
    oxygen: float, population_density: float
) -> float:
    """Оценка приспособленности (fitness) клетки"""
    metabolism = calculate_trait_value(dna, "metabolism_rate")
    division_speed = calculate_trait_value(dna, "division_speed")
    radiation_resist = calculate_trait_value(dna, "radiation_resistance")

    fitness = 1.0

    # Температура
    optimal_temp = 310  # K
    temp_penalty = abs(temp - optimal_temp) / 50
    fitness *= max(0.1, 1.0 - temp_penalty)

    # Радиация
    radiation_damage = radiation * (1.0 - radiation_resist)
    fitness *= max(0.1, 1.0 - radiation_damage * 0.1)

    # Питание
    if glucose < 0.2:
        fitness *= glucose / 0.2
    if oxygen < 0.2:
        fitness *= oxygen / 0.2

    # Плотность популяции (конкуренция)
    if population_density > 0.7:
        fitness *= (1.0 - (population_density - 0.7) * 2)

    # Умножаем на адаптивные черты
    fitness *= metabolism * division_speed

    return max(0.01, fitness)

@njit
def evolve_behavior(genome: str, sensor_input: np.ndarray) -> int:
    """Упрощённая эволюция поведения (нейросеть через ДНК)"""
    # Интерпретируем ДНК как веса сети
    total = 0.0
    for i in range(len(genome)):
        base = genome[i % len(genome)]
        weight = {'A': 1.0, 'C': -1.0, 'G': 0.5, 'T': -0.5}.get(base, 0.0)
        total += weight * sensor_input[i % len(sensor_input)]
    return 1 if total > 0 else 0

@njit(parallel=True)
def step_evolution(
    grid_type, grid_dna, grid_temp, grid_radiation,
    grid_glucose, grid_oxygen, grid_age, grid_fitness,
    h, w
):
    """
    Главный шаг эволюции — оценка приспособленности,
    мутации, отбор, репродукция
    """
    total_cells = 0
    avg_temp = 0.0
    avg_rad = 0.0

    # Сбор статистики по окружению
    for y in prange(h):
        for x in range(w):
            if grid_type[y, x] > 0:
                total_cells += 1
                avg_temp += grid_temp[y, x]
                avg_rad += grid_radiation[y, x]

    if total_cells == 0:
        return

    avg_temp /= total_cells
    avg_rad /= total_cells
    density = total_cells / (h * w)

    # Обновление каждой клетки
    for idx in prange(h * w):
        y = idx // w
        x = idx % w
        cell_type = grid_type[y, x]
        if cell_type == 0:
            continue

        dna = grid_dna[y, x]
        glucose = grid_glucose[y, x]
        oxygen = grid_oxygen[y, x]

        # Мутации
        dna = mutate_point(dna)
        dna = mutate_insertion(dna)
        dna = mutate_deletion(dna)
        grid_dna[y, x] = dna

        # Оценка приспособленности
        fitness = assess_fitness(dna, avg_temp, avg_rad, glucose, oxygen, density)
        grid_fitness[y, x] = fitness

        # Размножение (если достаточно зрелости)
        if grid_age[y, x] > 200 and np.random.rand() < fitness * 0.01:
            dx, dy = np.random.randint(-1, 2), np.random.randint(-1, 2)
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and grid_type[ny, nx] == 0:
                partner_dna = dna
                # Поиск партнёра рядом
                for ddy in (-1, 0, 1):
                    for ddx in (-1, 0, 1):
                        px, py = x + ddx, y + ddy
                        if 0 <= px < w and 0 <= py < h and grid_type[py, px] == cell_type:
                            partner_dna = grid_dna[py, px]
                            break

                child_dna = recombine(dna, partner_dna)
                child_dna = mutate_point(child_dna)
                child_dna = mutate_point(child_dna)  # двойная проверка

                grid_type[ny, nx] = cell_type
                grid_dna[ny, nx] = child_dna
                grid_age[ny, nx] = 0
                grid_fitness[ny, nx] = assess_fitness(
                    child_dna, avg_temp, avg_rad, glucose, oxygen, density
                )

        # Смерть слабых (естественный отбор)
        if np.random.rand() > fitness and grid_age[y, x] > 500:
            grid_type[y, x] = 0

@njit
def speciate(dna_list: list, threshold: float = 0.2) -> dict:
    """Кластеризация похожих геномов → виды"""
    species = {}
    species_id = 0
    for i, dna1 in enumerate(dna_list):
        assigned = False
        for sp_id, ref_dna in species.items():
            if sequence_similarity(dna1, ref_dna) > (1.0 - threshold):
                assigned = True
                break
        if not assigned:
            species[species_id] = dna1
            species_id += 1
    return species

@njit
def sequence_similarity(dna1: str, dna2: str) -> float:
    """Сходство двух ДНК последовательностей"""
    if len(dna1) == 0 or len(dna2) == 0:
        return 0.0
    matches = 0
    length = min(len(dna1), len(dna2))
    for i in range(length):
        if dna1[i] == dna2[i]:
            matches += 1
    return matches / length

@njit
def log_evolution_event(event_type: str, details: str):
    """Заглушка для логирования (в реальной версии пишет в файл)"""
    pass