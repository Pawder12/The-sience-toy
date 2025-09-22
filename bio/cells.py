# bio/cells.py
import numpy as np
from numba import njit, prange
import random

# Константы
MEV_TO_KELVIN = 1.16045e7
GLUCOSE_THRESHOLD = 0.5
OXYGEN_THRESHOLD = 0.3
DAMAGE_THRESHOLD = 100
MAX_TELomERE = 10000
TELOMERE_LOSS_PER_DIVISION = 200

@njit
def mutate_dna(dna: str, rate: float = 0.001) -> str:
    """Мутирует ДНК с заданной вероятностью на каждый нуклеотид"""
    bases = "ACGT"
    result = ""
    for base in dna:
        if np.random.rand() < rate:
            # Замена на случайный, но не такой же
            new_base = np.random.choice([b for b in bases if b != base])
            result += new_base
        else:
            result += base
    return result

@njit
def transcribe_gene(dna: str, gene_start: int, gene_end: int) -> str:
    """Транскрипция ДНК в РНК (упрощённо)"""
    gene = dna[gene_start:gene_end]
    rna = gene.replace('T', 'U')
    return rna

@njit
def translate_rna(rna: str) -> str:
    """Перевод РНК в белок по генетическому коду (упрощённо)"""
    codon_table = {
        "UUU": "Phe", "UUC": "Phe", "UUA": "Leu", "UUG": "Leu",
        "UCU": "Ser", "UCC": "Ser", "UCA": "Ser", "UCG": "Ser",
        "UAU": "Tyr", "UAC": "Tyr", "UAA": "*", "UAG": "*",
        "UGU": "Cys", "UGC": "Cys", "UGA": "*", "UGG": "Trp",
        "CUU": "Leu", "CUC": "Leu", "CUA": "Leu", "CUG": "Leu",
        "CCU": "Pro", "CCC": "Pro", "CCA": "Pro", "CCG": "Pro",
        "CAU": "His", "CAC": "His", "CAA": "Gln", "CAG": "Gln",
        "CGU": "Arg", "CGC": "Arg", "CGA": "Arg", "CGG": "Arg",
        "AUU": "Ile", "AUC": "Ile", "AUA": "Ile", "AUG": "Met",
        "ACU": "Thr", "ACC": "Thr", "ACA": "Thr", "ACG": "Thr",
        "AAU": "Asn", "AAC": "Asn", "AAA": "Lys", "AAG": "Lys",
        "AGU": "Ser", "AGC": "Ser", "AGA": "Arg", "AGG": "Arg",
        "GUU": "Val", "GUC": "Val", "GUA": "Val", "GUG": "Val",
        "GCU": "Ala", "GCC": "Ala", "GCA": "Ala", "GCG": "Ala",
        "GAU": "Asp", "GAC": "Asp", "GAA": "Glu", "GAG": "Glu",
        "GGU": "Gly", "GGC": "Gly", "GGA": "Gly", "GGG": "Gly"
    }
    protein = ""
    for i in range(0, len(rna) - 2, 3):
        codon = rna[i:i+3]
        if len(codon) == 3:
            amino = codon_table.get(codon, "X")
            if amino == "*":
                break
            protein += amino + "-"
    return protein if protein else "None"

@njit
def cell_metabolism(glucose, oxygen, waste, x, y, h, w):
    """Обновляет уровень энергии и производит отходы"""
    if glucose[y, x] > GLUCOSE_THRESHOLD and oxygen[y, x] > OXYGEN_THRESHOLD:
        energy = 0.02
        waste[y, x] += 0.015  # CO2
        lactate_loss = 0.0
    else:
        energy = 0.005  # анаэробное дыхание
        waste[y, x] += 0.02
        lactate_loss = 0.01
    return energy, lactate_loss

@njit
def update_stem_cell(
    grid_type, grid_dna, grid_telomere, grid_age, grid_glucose,
    grid_oxygen, grid_waste, vx, vy, x, y, h, w
):
    """Стволовая клетка: может делиться или дифференцироваться"""
    if grid_age[y, x] < 100:
        return

    # Потеря теломер
    grid_telomere[y, x] -= TELOMERE_LOSS_PER_DIVISION
    if grid_telomere[y, x] <= 0:
        grid_type[y, x] = 0  # старческая смерть
        return

    # Мутация ДНК
    if np.random.rand() < 0.01:
        grid_dna[y, x] = mutate_dna(grid_dna[y, x], rate=0.005)

    # Деление
    dx, dy = np.random.randint(-1, 2), np.random.randint(-1, 2)
    nx, ny = x + dx, y + dy
    if 0 <= nx < w and 0 <= ny < h and grid_type[ny, ny] == 0:
        grid_type[ny, nx] = 100  # новая стволовая
        grid_dna[ny, nx] = grid_dna[y, x]
        grid_telomere[ny, nx] = grid_telomere[y, x]
        grid_age[ny, nx] = 0

    # Дифференцировка под сигналом
    if grid_glucose[y, x] < 0.4:
        grid_type[y, x] = 103  # эпителий
    elif grid_oxygen[y, x] < 0.2:
        grid_type[y, x] = 104  # эритроцит
    elif np.random.rand() < 0.001:
        grid_type[y, x] = 101  # нейрон

    grid_age[y, x] = 0

@njit
def update_neuron(
    grid_type, membrane_potential, synaptic_queue,
    grid_temp, x, y, h, w
):
    """Нейрон: потенциал действия, передача сигнала"""
    resting = -70
    threshold = -55
    firing = 40
    decay = 0.99

    v = membrane_potential[y, x]

    # Инжекция от соседа
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                if grid_type[ny, nx] == 101 and synaptic_queue[ny, nx] > 0:
                    v += 10

    if v > threshold:
        membrane_potential[y, x] = firing
        synaptic_queue[y, x] = 5  # очередь передачи
        grid_temp[y, x] += 0.5  # нагрев при активности
    else:
        membrane_potential[y, x] = v * decay + resting * (1 - decay)

    if synaptic_queue[y, x] > 0:
        synaptic_queue[y, x] -= 1

@njit
def update_muscle_fiber(
    grid_type, contraction_state, calcium, force_map,
    x, y, h, w
):
    """Мышца: сокращается при сигнале"""
    if calcium[y, x] > 0.5:
        contraction_state[y, x] = min(contraction_state[y, x] + 0.1, 1.0)
    else:
        contraction_state[y, x] *= 0.95

    # Создание силы
    if contraction_state[y, x] > 0.5:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    force_map[ny, nx] += contraction_state[y, x] * 0.1

@njit
def update_immune_cell(
    grid_type, grid_chemotaxis, pathogen_map, x, y, h, w
):
    """Лейкоцит: движется к инфекции, фагоцитирует"""
    if pathogen_map[y, x] > 0.1:
        # Хемотаксис
        best_dx, best_dy = 0, 0
        max_pathogen = pathogen_map[y, x]
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    if pathogen_map[ny, nx] > max_pathogen:
                        max_pathogen = pathogen_map[ny, nx]
                        best_dx, best_dy = dx, dy
        grid_type[y + best_dy, x + best_dx] = 105
        grid_type[y, x] = 0

@njit
def update_virus(
    grid_type, grid_dna, grid_host, infection_timer,
    x, y, h, w
):
    """Вирус: заражает клетку, реплицируется"""
    for dy in range(-5, 6):
        for dx in range(-5, 6):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                if grid_type[ny, nx] in [100, 101, 102, 103] and np.random.rand() < 0.1:
                    grid_host[ny, nx] = 107  # заражён
                    infection_timer[ny, nx] = 300
                    grid_type[y, x] = 0  # вирус исчезает
                    return

@njit
def update_cancer_cell(
    grid_type, grid_dna, grid_age, x, y, h, w
):
    """Раковая клетка: бесконтрольное деление"""
    if grid_age[y, x] % 50 == 0:
        for _ in range(2):
            dx, dy = np.random.randint(-1, 2), np.random.randint(-1, 2)
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and grid_type[ny, nx] == 0:
                grid_type[ny, nx] = 106
                grid_dna[ny, nx] = mutate_dna(grid_dna[y, x], rate=0.02)
                break

@njit
def update_photosynthetic_cell(
    grid_type, grid_light, glucose, oxygen, x, y, h, w
):
    """Фотосинтез: свет → глюкоза + кислород"""
    if grid_light[y, x] > 0.5:
        glucose[y, x] = min(glucose[y, x] + 0.005, 1.0)
        oxygen[y, x] = min(oxygen[y, x] + 0.008, 1.0)

@njit(parallel=True)
def step_cells(
    grid_type, grid_dna, grid_telomere, grid_age,
    membrane_potential, synaptic_queue, contraction_state,
    calcium, force_map, pathogen_map, infection_timer,
    glucose, oxygen, waste, light, h, w
):
    """Главный шаг обновления всех клеток"""
    for idx in prange(h * w):
        y = idx // w
        x = idx % w
        cell_type = grid_type[y, x]

        if cell_type == 100:  # Stem Cell
            update_stem_cell(
                grid_type, grid_dna, grid_telomere, grid_age,
                glucose, oxygen, waste, None, None, x, y, h, w
            )
        elif cell_type == 101:  # Neuron
            update_neuron(
                grid_type, membrane_potential, synaptic_queue,
                None, x, y, h, w
            )
        elif cell_type == 102:  # Muscle
            update_muscle_fiber(
                grid_type, contraction_state, calcium, force_map,
                x, y, h, w
            )
        elif cell_type == 105:  # Immune
            update_immune_cell(
                grid_type, None, pathogen_map, x, y, h, w
            )
        elif cell_type == 107:  # Virus
            update_virus(
                grid_type, grid_dna, None, infection_timer,
                x, y, h, w
            )
        elif cell_type == 106:  # Cancer
            update_cancer_cell(
                grid_type, grid_dna, grid_age, x, y, h, w
            )
        elif cell_type == 110:  # Photosynthetic
            update_photosynthetic_cell(
                grid_type, light, glucose, oxygen, x, y, h, w
            )

        if cell_type > 0:
            grid_age[y, x] += 1