# constants.py
"""
The Particle Simulator — Глобальные константы
(c) 2025 | Полная научная конфигурация
"""

# === 🖥️ ОСНОВНЫЕ РАЗМЕРЫ ЭКРАНА И СЕТКИ ===
WINDOW_WIDTH = 1400        # Общая ширина окна
WINDOW_HEIGHT = 900        # Высота окна
PANEL_WIDTH = 240          # Левая панель управления
SIM_AREA_WIDTH = WINDOW_WIDTH - PANEL_WIDTH  # Рабочая зона симуляции

# Размер ячейки (в пикселях). 1 = максимальное разрешение
CELL_SIZE = 1

# Размер сетки (в ячейках)
GRID_W = SIM_AREA_WIDTH // CELL_SIZE  # 1160 при CELL_SIZE=1
GRID_H = WINDOW_HEIGHT // CELL_SIZE   # 900

# Максимальное количество элементов (ограничение ID)
MAX_ELEMENT_ID = 255


# === 🔬 ФИЗИЧЕСКИЕ КОНСТАНТЫ (SI + масштабирование) ===
G_ACCEL = 9.81                     # Ускорение свободного падения (м/с²)
G_SCALE = 0.1                      # Масштаб для симуляции (пикс/с²)
GRAVITY = G_ACCEL * G_SCALE        # Применяемое ускорение

K_B = 1.380649e-23                 # Постоянная Больцмана (Дж/K)
STEFAN_BOLTZMANN = 5.670374419e-8  # Вт/(м²·К⁴)
MEV_TO_KELVIN = 1.160451812e7      # 1 МэВ = ~11.6 миллионов К

ABSOLUTE_ZERO_C = -273.15          # 0 K = -273.15 °C
ROOM_TEMP_K = 298.0                # 25 °C

# Давление
ATMOSPHERIC_PRESSURE_PA = 101325   # 1 атм в Паскалях
PRESSURE_SCALE = 1e-5              # Масштаб давления для визуализации

# Теплопроводность по умолчанию (Вт/м·К)
DEFAULT_THERMAL_CONDUCTIVITY = 0.1
DEFAULT_EMISSIVITY = 0.9


# === ⚛️ ОСНОВНЫЕ ID ЭЛЕМЕНТОВ (должны соответствовать JSON) ===
AIR = 0
WALL = 1
SAND = 2
WATER = 3
FIRE = 4
SMOKE = 5
PLANT = 7
ELECTRON = 8
DIS = 9             # Destroy (лазер удаления)

# === 💧 ЖИДКОСТИ И ГАЗЫ ===
WATER_VAPOR = 30
HYDROGEN = 10
OXYGEN = 11
ACID = 15
OIL = 16
LAVA = 17

# === 🧱 ТВЁРДЫЕ МАТЕРИАЛЫ ===
IRON = 13
COPPER = 14
GLASS = 63
RUBBER = 60
SILICONE = 61
STEEL_SPRING = 62
FOAM = 65
CARBON_DIOXIDE_ICE = 66  # Сухой лёд

# === ⚡ ЭЛЕКТРИЧЕСТВО И ЭНЕРГИЯ ===
BATTERY_POS = 202
BATTERY_NEG = 201
WIRE = 13           # Iron как проводник
LED_RED = 210
LED_GREEN = 211
TRANSISTOR = 212
CAPACITOR = 213

# === ☢️ ЯДЕРНЫЕ ЭЛЕМЕНТЫ ===
URANIUM_235 = 50
URANIUM_238 = 51
PLUTONIUM_239 = 52
NEUTRON = 54
GAMMA_RAY = 59
CESIUM_137 = 60
IODINE_131 = 61
STRONTIUM_90 = 62
BORON_CONTROL_ROD = 63
MODERATOR_WATER = 64
MODERATOR_GRAPHITE = 65
FUSION_PLASMA = 67

# === 🧫 БИОЛОГИЯ ===
STEM_CELL = 100
NEURON = 101
MUSCLE_FIBER = 102
EPITHELIAL_CELL = 103
BLOOD_CELL = 104
IMMUNE_CELL = 105
CANCER_CELL = 106
VIRUS = 107
PHOTOSYNTHETIC_CELL = 110
SYNTHETIC_CIRCUIT = 109

# === 🌀 ПОЛЯ И ЭКЗОТИКА ===
GRAVITY_SOURCE = 200
ANTI_GRAVITY = 201
LASER_BEAM = 215
LENS = 216
BLACK_HOLE = 217
DARK_MATTER = 213
VORTEX = 214

# === 🛠️ ИНСТРУМЕНТЫ (не сохраняются в grid.type) ===
BRUSH_TOOL = 999
PAN_TOOL = 998
PICKER_TOOL = 997
WIPE_TOOL = 996


# === 🎨 ЦВЕТА ПО УМОЛЧАНИЮ (RGB) ===
ELEMENT_COLORS = {
    # --- Основные ---
    AIR: (0, 0, 0),
    WALL: (80, 80, 80),
    SAND: (240, 220, 80),
    WATER: (0, 100, 255),
    FIRE: (255, 50, 5),
    SMOKE: (100, 100, 100),
    PLANT: (20, 180, 20),
    ELECTRON: (255, 255, 0),
    DIS: (255, 0, 255),

    # --- Жидкости ---
    ACID: (200, 255, 0),
    OIL: (150, 100, 50),
    LAVA: (255, 60, 0),

    # --- Металлы ---
    IRON: (180, 100, 50),
    COPPER: (200, 100, 0),
    STEEL_SPRING: (160, 160, 180),
    RUBBER: (180, 30, 30),
    SILICONE: (220, 220, 220),
    FOAM: (240, 240, 240),

    # --- Ядерные ---
    URANIUM_235: (0, 180, 0),
    URANIUM_238: (20, 100, 0),
    PLUTONIUM_239: (180, 0, 0),
    NEUTRON: (255, 255, 255),
    GAMMA_RAY: (255, 255, 255),
    CESIUM_137: (100, 100, 200),
    IODINE_131: (200, 50, 200),
    STRONTIUM_90: (150, 150, 100),
    BORON_CONTROL_ROD: (100, 50, 0),

    # --- Биология ---
    STEM_CELL: (220, 180, 255),
    NEURON: (100, 150, 255),
    MUSCLE_FIBER: (200, 50, 50),
    BLOOD_CELL: (255, 60, 60),
    IMMUNE_CELL: (255, 255, 255),
    CANCER_CELL: (255, 0, 100),
    VIRUS: (0, 255, 0),
    PHOTOSYNTHETIC_CELL: (50, 200, 50),

    # --- Поля ---
    GRAVITY_SOURCE: (100, 0, 255),
    ANTI_GRAVITY: (0, 255, 255),
    LASER_BEAM: (255, 255, 0),
    BLACK_HOLE: (0, 0, 0),
    VORTEX: (100, 100, 255),
}

# === 🎨 ЦВЕТА ИНТЕРФЕЙСА ===
COLOR_BG = (15, 15, 30)           # Фон
COLOR_PANEL = (30, 30, 50)         # Панель
COLOR_TEXT = (220, 220, 220)       # Текст
COLOR_BORDER = (100, 100, 150)     # Границы
COLOR_HIGHLIGHT = (255, 255, 100)  # Подсветка
COLOR_BUTTON = (60, 60, 90)
COLOR_BUTTON_HOVER = (90, 90, 130)
COLOR_ERROR = (255, 80, 80)
COLOR_SUCCESS = (100, 200, 100)
COLOR_WARNING = (255, 180, 0)


# === ⏱️ НАСТРОЙКИ СИМУЛЯЦИИ ===
FPS = 60                           # Целевой FPS
MAX_SUBSTEPS = 3                   # Макс подшагов при перегрузке
ENABLE_GRAVITY = True
ENABLE_PRESSURE = True
ENABLE_HEAT_TRANSFER = True
ENABLE_ELECTRICITY = True
ENABLE_NUCLEAR = True
ENABLE_BIOLOGY = True
ENABLE_FLUID_DYNAMICS = True

# Автосохранение
AUTOSAVE_ENABLED = True
AUTOSAVE_INTERVAL_SECONDS = 10
AUTOSAVE_FILENAME = "autosave.tps"

# Размер кисти
MIN_BRUSH_SIZE = 1
MAX_BRUSH_SIZE = 100
DEFAULT_BRUSH_SIZE = 4


# === 📊 РЕЖИМЫ ОТОБРАЖЕНИЯ ===
RENDER_MODES = [
    "normal",
    "ir",           # Инфракрасный (температура)
    "pressure",     # Давление
    "velocity",     # Скорость потока
    "radiation",    # Радиоактивное заражение
    "electric",     # Электрическое поле
    "magnetic",     # Магнитное поле
]

# Названия режимов для UI
RENDER_MODE_NAMES = {
    "normal": "Обычный",
    "ir": "ИК-режим",
    "pressure": "Давление",
    "velocity": "Скорость",
    "radiation": "Радиация",
    "electric": "Электричество",
    "magnetic": "Магнетизм",
}


# === 🔬 НАУЧНЫЕ ПОРОГИ И ЗНАЧЕНИЯ ===
CRITICAL_RADIUS_U235_PX = 8        # Радиус для цепной реакции (U-235)
HALF_LIFE_CS137_S = 9467000       # 263 дня
HALF_LIFE_I131_S = 604800          # 7 дней
DAMAGE_THRESHOLD = 100             # Порог радиационного повреждения клеток
METABOLISM_GLUCOSE_THRESHOLD = 0.5
OXYGEN_MIN_FOR_AEROBIC = 0.3


# === 🐞 ОТЛАДКА ===
DEBUG_MODE = False
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
ENABLE_PROFILING = False
SHOW_FPS = True
ENABLE_GRID_SNAP = False


# === 🧩 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def kelvin_to_celsius(k):
    """Перевод Кельвинов в Цельсии"""
    return k + ABSOLUTE_ZERO_C

def celsius_to_kelvin(c):
    """Перевод Цельсия в Кельвины"""
    return c - ABSOLUTE_ZERO_C

def rgb_to_hex(rgb):
    """RGB кортеж → HEX строка"""
    r, g, b = [max(0, min(255, int(x))) for x in rgb]
    return f"#{r:02x}{g:02x}{b:02x}"

def hex_to_rgb(hex_color):
    """HEX строка → RGB кортеж"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# === ✅ ПРОВЕРКА ЗАГРУЗКИ (для теста) ===
if __name__ == "__main__":
    print("✅ constants.py — успешно загружен")
    print(f"Размер окна: {WINDOW_WIDTH} × {WINDOW_HEIGHT}")
    print(f"Размер сетки: {GRID_W} × {GRID_H}")
    print(f"Количество элементов: {len(ELEMENT_COLORS)}")
    print(f"Режимы отображения: {RENDER_MODES}")
    print(f"Пример цвета Sand: {ELEMENT_COLORS[SAND]}")