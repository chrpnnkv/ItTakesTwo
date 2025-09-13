import pygame as pg
from .resources import font

class Button:
    def __init__(self, rect, text, on_click):
        self.rect = pg.Rect(rect)
        self.text = text
        self.on_click = on_click

    def draw(self, surface):
        pg.draw.rect(surface, (30,30,30), self.rect, border_radius=8)
        pg.draw.rect(surface, (200,200,200), self.rect, 2, border_radius=8)
        label = font("better-vcr-5.2.ttf", 24).render(self.text, True, (240,240,240))
        surface.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()
