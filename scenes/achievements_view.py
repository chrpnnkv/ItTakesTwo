import pygame as pg
from core.base_scene import BaseScene
from core.ui import Button

ACHI_LIST = [
    ("da_ya_zhestkii", "Да я жёсткий"),
    ("skulptura", "Скульптура из мусора"),
    ("stertye_nogi", "Стертые ноги"),
    ("pryaniki", "Пряники"),
    ("lyagyshka", "Лягушонок"),
    ("coat", "Зато шубка есть")
]

class AchievementsView(BaseScene):
    def __init__(self, manager, state):
        super().__init__(manager)
        self.state = state
        self.back = Button((20, 20, 140, 40), "Назад",
                           lambda: pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_ESCAPE)))

    def handle_event(self, e):
        if e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
            from scenes.menu import MenuScene
            self.mgr.switch(MenuScene)
        self.back.handle_event(e)

    def draw(self):
        self.screen.fill((16,16,20))
        self.back.draw(self.screen)
        y = 100
        for key, title in ACHI_LIST:
            opened = key in self.state.achievements
            color = (230,255,130) if opened else (120,120,120)
            pg.draw.circle(self.screen, color, (80, y+10), 8)
            font = pg.font.SysFont(None, 28)
            self.screen.blit(font.render(title, True, color), (100, y))
            y += 40
