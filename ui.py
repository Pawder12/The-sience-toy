# ui.py
import pygame
import numpy as np
from typing import List, Dict, Any, Optional
from constants import *

class Button:
    """Универсальная кнопка с hover-эффектами"""
    def __init__(self, x, y, w, h, text, action=None, color=(70, 70, 100), hover_color=(100, 100, 150)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action
        self.color = color
        self.hover_color = hover_color
        self.font = pygame.font.SysFont(None, 20)
        self.visible = True
        self.enabled = True

    def draw(self, screen):
        if not self.visible:
            return
        color = self.hover_color if self.is_hovered() else self.color
        border_color = (200, 200, 200) if self.enabled else (80, 80, 80)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, border_color, self.rect, 2)

        text_surf = self.font.render(self.text, True, (240, 240, 240))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_hovered(self):
        if not self.enabled:
            return False
        mx, my = pygame.mouse.get_pos()
        return self.rect.collidepoint(mx, my)

    def is_clicked(self, event):
        return self.enabled and event.type == pygame.MOUSEBUTTONDOWN and self.is_hovered()


class Notification:
    """Система уведомлений (всплывающие сообщения)"""
    def __init__(self, text: str, duration: int = 180, color=(100, 200, 100)):
        self.text = text
        self.frames_left = duration
        self.color = color
        self.font = pygame.font.SysFont(None, 18)

    def draw(self, screen, x, y):
        if self.frames_left <= 0:
            return
        shadow = self.font.render(self.text, True, (0, 0, 0))
        text = self.font.render(self.text, True, self.color)
        screen.blit(shadow, (x + 1, y + 1))
        screen.blit(text, (x, y))

    def update(self):
        self.frames_left -= 1


class UIBrushPreview:
    """Превью кисти в реальном времени"""
    def __init__(self):
        self.visible = False
        self.x = 0
        self.y = 0
        self.radius = 0
        self.color = (255, 255, 255)

    def show(self, x, y, radius, color=None):
        self.visible = True
        self.x = x
        self.y = y
        self.radius = radius
        if color:
            self.color = color

    def hide(self):
        self.visible = False

    def draw(self, screen):
        if self.visible:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius, 1)


class UI:
    """
    Главный пользовательский интерфейс.
    Включает панель выбора элементов, режимов, кисть, уведомления.
    """

    def __init__(self, grid, elements: Dict[int, dict]):
        self.grid = grid
        self.elements = elements
        self.selected_element = AIR
        self.brush_size = 3
        self.notifications: List[Notification] = []
        self.buttons: List[Button] = []
        self.brush_preview = UIBrushPreview()

        # Шрифты
        self.font_large = pygame.font.SysFont(None, 28)
        self.font_medium = pygame.font.SysFont(None, 22)
        self.font_small = pygame.font.SysFont(None, 18)

        # Создание кнопок
        self._create_buttons()

        # Цвета интерфейса
        self.colors = {
            "panel_bg": (30, 30, 50),
            "text": (220, 220, 220),
            "border": (100, 100, 150),
            "highlight": (255, 255, 100),
            "disabled": (80, 80, 100)
        }

    def _create_buttons(self):
        """Создаёт все кнопки интерфейса"""
        y_start = WINDOW_HEIGHT - 150
        btn_w, btn_h = 90, 25

        self.buttons.append(Button(
            PANEL_WIDTH // 4 - btn_w // 2, y_start,
            btn_w, btn_h, "Save", self.save_world, (60, 100, 60)))
        self.buttons.append(Button(
            3 * PANEL_WIDTH // 4 - btn_w // 2, y_start,
            btn_w, btn_h, "Load", self.load_world, (60, 60, 100)))

        self.buttons.append(Button(
            PANEL_WIDTH // 4 - btn_w // 2, y_start + 30,
            btn_w, btn_h, "Clear", self.clear_grid, (100, 60, 60)))

        self.buttons.append(Button(
            3 * PANEL_WIDTH // 4 - btn_w // 2, y_start + 30,
            btn_w, btn_h, "Undo", self.undo_action, (80, 80, 80), (100, 100, 100)))

    def save_world(self):
        try:
            import io_module
            io_module.save_world(self.grid, "autosave.tps")
            self.add_notification("Сохранено: autosave.tps")
        except Exception as e:
            self.add_notification(f"Ошибка: {str(e)}", error=True)

    def load_world(self):
        try:
            import io_module
            io_module.load_world(self.grid, "autosave.tps")
            self.add_notification("Загружено: autosave.tps")
        except Exception as e:
            self.add_notification(f"Ошибка загрузки", error=True)

    def clear_grid(self):
        self.grid.clear()
        self.add_notification("Сетка очищена")

    def undo_action(self):
        self.add_notification("Отмена пока не реализована", error=True)

    def add_notification(self, text: str, error: bool = False, duration: int = 180):
        """Добавляет новое уведомление"""
        color = (255, 80, 80) if error else (100, 200, 100)
        self.notifications.append(Notification(text, duration, color))

    def handle_event(self, event, renderer):
        """Обработка всех событий UI"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ЛКМ
                mx, my = event.pos
                if mx < PANEL_WIDTH:
                    selected = self.handle_click(mx, my)
                    if selected is not None:
                        self.selected_element = selected
                        self.add_notification(f"Выбрано: {self.elements[selected]['name']}")
                else:
                    self.brush_preview.hide()

            elif event.button == 4:  # Колесо вверх
                self.brush_size = min(self.brush_size + 1, 20)
            elif event.button == 5:  # Колесо вниз
                self.brush_size = max(self.brush_size - 1, 1)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:
                renderer.toggle_mode('ir')
                mode = "IR" if renderer.modes['ir'] else "Normal"
                self.add_notification(f"Режим: {mode}")
            elif event.key == pygame.K_p:
                renderer.toggle_mode('pressure')
                mode = "Pressure" if renderer.modes['pressure'] else "Normal"
                self.add_notification(f"Режим: {mode}")
            elif event.key == pygame.K_r:
                renderer.toggle_mode('radiation')
                mode = "Radiation" if renderer.modes['radiation'] else "Normal"
                self.add_notification(f"Режим: {mode}")

        # Обработка кнопок
        for btn in self.buttons:
            if btn.is_clicked(event):
                if btn.action:
                    btn.action()

    def handle_click(self, mx: int, my: int) -> Optional[int]:
        """Проверяет, нажал ли пользователь на элемент"""
        start_y = 40
        elem_per_row = 4
        item_h = 30
        item_w = 50

        for i, elem_id in enumerate(self.elements.keys()):
            row = i // elem_per_row
            col = i % elem_per_row
            x = 10 + col * (item_w + 10)
            y = start_y + row * item_h

            if x <= mx <= x + item_w and y <= my <= y + item_h:
                return elem_id
        return None

    def draw_elements_panel(self, screen):
        """Отрисовка панели элементов"""
        start_y = 40
        elem_per_row = 4
        item_h, item_w = 30, 50

        label = self.font_medium.render("Элементы:", True, self.colors["text"])
        screen.blit(label, (10, 20))

        for i, (elem_id, props) in enumerate(self.elements.items()):
            row = i // elem_per_row
            col = i % elem_per_row
            x = 10 + col * (item_w + 10)
            y = start_y + row * item_h

            # Фон
            rect = pygame.Rect(x, y, item_w, item_h)
            pygame.draw.rect(screen, (50, 50, 70), rect)
            if elem_id == self.selected_element:
                pygame.draw.rect(screen, self.colors["highlight"], rect, 2)
            else:
                pygame.draw.rect(screen, self.colors["border"], rect, 1)

            # Цвет элемента
            color_rect = pygame.Rect(x + 5, y + 5, 20, 20)
            pygame.draw.rect(screen, props["color"], color_rect)

            # Название
            name = props["name"][:7]
            text = self.font_small.render(name, True, self.colors["text"])
            screen.blit(text, (x + 30, y + 8))

    def draw_controls(self, screen):
        """Отрисовка элементов управления"""
        y = 20
        screen.blit(self.font_medium.render("Управление:", True, self.colors["text"]), (10, y))
        y += 25

        controls = [
            ("ЛКМ", "Рисовать"),
            ("ПКМ", "Ластик"),
            ("Колесо", "Размер кисти"),
            ("Ctrl+S", "Сохранить"),
            ("Ctrl+L", "Загрузить"),
            ("I/P/R", "Режимы")
        ]

        for key, desc in controls:
            key_text = self.font_small.render(key, True, (180, 180, 100))
            desc_text = self.font_small.render(desc, True, self.colors["text"])
            screen.blit(key_text, (15, y))
            screen.blit(desc_text, (60, y))
            y += 18

    def draw_status(self, screen, fps: float):
        """Отрисовка статуса"""
        y = WINDOW_HEIGHT - 200
        active_mode = "Normal"
        for mode, enabled in renderer.modes.items():
            if enabled and mode != 'normal':
                active_mode = mode.capitalize()

        status_lines = [
            f"FPS: {int(fps)}",
            f"Кисть: {self.brush_size}",
            f"Режим: {active_mode}",
            f"Элемент: {self.elements[self.selected_element]['name']}"
        ]

        for line in status_lines:
            text = self.font_small.render(line, True, self.colors["text"])
            screen.blit(text, (10, y))
            y += 18

    def draw(self, screen, mx: int, my: int, renderer, clock):
        """Главная функция отрисовки UI"""
        # Фон панели
        panel_rect = pygame.Rect(0, 0, PANEL_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(screen, self.colors["panel_bg"], panel_rect)
        pygame.draw.line(screen, self.colors["border"], (PANEL_WIDTH, 0), (PANEL_WIDTH, WINDOW_HEIGHT), 2)

        # Заголовок
        title = self.font_large.render("TPS", True, (255, 215, 0))
        subtitle = self.font_small.render("The Particle Simulator", True, (150, 200, 255))
        screen.blit(title, (PANEL_WIDTH // 2 - title.get_width() // 2, 5))
        screen.blit(subtitle, (PANEL_WIDTH // 2 - subtitle.get_width() // 2, 30))

        # Элементы
        self.draw_elements_panel(screen)

        # Управление
        self.draw_controls(screen)

        # Статус
        self.draw_status(screen, clock.get_fps())

        # Кнопки
        for btn in self.buttons:
            btn.draw(screen)

        # Уведомления
        for i, note in enumerate(self.notifications):
            note.update()
            note.draw(screen, 10, WINDOW_HEIGHT - 50 + i * 20)

        # Очистка уведомлений
        self.notifications = [n for n in self.notifications if n.frames_left > 0]

        # Превью кисти
        if mx >= PANEL_WIDTH and self.brush_size > 0:
            scaled_x = (mx - PANEL_WIDTH) * self.grid.w / (WINDOW_WIDTH - PANEL_WIDTH)
            scaled_y = my * self.grid.h / WINDOW_HEIGHT
            pixel_x = int(scaled_x) * CELL_SIZE + PANEL_WIDTH
            pixel_y = int(scaled_y) * CELL_SIZE
            radius_px = self.brush_size * CELL_SIZE
            self.brush_preview.show(pixel_x, pixel_y, radius_px)
        else:
            self.brush_preview.hide()

        self.brush_preview.draw(screen)