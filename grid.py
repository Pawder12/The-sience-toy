# grid.py
import numpy as np

class Grid:
    def __init__(self, w=600, h=600):
        self.w, self.h = w, h
        
        # Основные поля
        self.type = np.zeros((h, w), dtype=np.uint8)          # тип материала
        self.temp = np.full((h, w), 298.0)                   # температура (K)
        self.life = np.zeros((h, w), dtype=np.int32)         # "жизнь" (огонь, вирусы)
        
        # Динамика жидкостей и газов
        self.vx = np.zeros((h, w), dtype=np.float32)         # скорость X
        self.vy = np.zeros((h, w), dtype=np.float32)         # скорость Y
        self.pressure = np.full((h, w), 101325.0)            # давление (Па)
        self.density = np.ones((h, w), dtype=np.float32)     # плотность
        
        # Электричество и магнетизм
        self.conductivity = np.zeros((h, w), dtype=np.float32)  # проводимость
        self.charge = np.zeros((h, w), dtype=np.float32)     # заряд
        self.magnetic_field_x = np.zeros((h, w), dtype=np.float32)
        self.magnetic_field_y = np.zeros((h, w), dtype=np.float32)
        
        # Радиация и повреждения
        self.radiation = np.zeros((h, w), dtype=np.float32)  # излучение (заряд/см²)
        self.damage = np.zeros((h, w), dtype=np.float32)     # повреждение клеток
        self.age = np.zeros((h, w), dtype=np.int32)          # возраст клетки
        
        # Биология
        self.dna = np.empty((h, w), dtype=object)            # ДНК как строка
        self.telomere = np.full((h, w), 10000, dtype=np.int32)  # теломеры
        self.fitness = np.ones((h, w), dtype=np.float32)     # приспособленность
        
        # Вспомогательные
        self.heat_source = np.zeros((h, w), dtype=np.float32)  # внешний нагрев
        self.emissivity = np.full((h, w), 0.9, dtype=np.float32)  # коэффициент излучения
        
        # Инициализация DNA
        for y in range(h):
            for x in range(w):
                self.dna[y, x] = ""

    def clear(self):
        """Очистить сетку"""
        self.type.fill(0)
        self.temp.fill(298.0)
        self.life.fill(0)
        self.vx.fill(0)
        self.vy.fill(0)
        self.pressure.fill(101325.0)
        self.radiation.fill(0)
        self.damage.fill(0)
        self.age.fill(0)
        self.fitness.fill(1.0)
        self.heat_source.fill(0)
    
    def copy_region(self, src_x, src_y, dst_x, dst_y, w, h):
        """Копировать область"""
        if (src_x >= 0 and src_y >= 0 and dst_x >= 0 and dst_y >= 0 and
            src_x + w <= self.w and src_y + h <= self.h and
            dst_x + w <= self.w and dst_y + h <= self.h):
            self.type[dst_y:dst_y+h, dst_x:dst_x+w] = \
                self.type[src_y:src_y+h, src_x:src_x+w].copy()
            self.temp[dst_y:dst_y+h, dst_x:dst_x+w] = \
                self.temp[src_y:src_y+h, src_x:src_x+w].copy()