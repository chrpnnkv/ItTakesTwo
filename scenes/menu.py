import pygame as pg
from core.base_scene import BaseScene
from core.ui import Button
from core.state import GameState
from scenes.cutscene import CutsceneScene
from scenes.achievements_view import AchievementsView

class MenuScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.state = GameState()
        w, h = self.screen.get_size()
        cx = w//2
        self.buttons = [
            Button((cx-120, 180, 240, 48), "Начать", lambda: self.mgr.switch(
                CutsceneScene, state=self.state, script_file="script_ch1.json", next_scene="concert")),
            Button((cx - 120, 240, 240, 48), "Продолжить", self._resume),
            Button((cx-120, 300, 240, 48), "Ачивки", lambda: self.mgr.switch(AchievementsView, state=self.state)),
            Button((cx-120, 360, 240, 48), "Выход", lambda: pg.event.post(pg.event.Event(pg.QUIT)))
        ]

    def handle_event(self, e):
        for b in self.buttons: b.handle_event(e)

    def draw(self):
        self.screen.fill((12,12,16))
        for b in self.buttons: b.draw(self.screen)

    def _resume(self):
        self.state.load()
        # примитивная логика: если есть обе ачивки — в финал, если одна — к лабиринту, иначе — в самую первую кат-сцену
        if "stertye_nogi" in self.state.achievements:
            self.mgr.switch(AchievementsView, state=self.state)
        elif "da_ya_zhestkii" in self.state.achievements:
            from scenes.cutscene import CutsceneScene
            self.mgr.switch(CutsceneScene, state=self.state, script_file="script_ch2.json", next_scene="maze")
        else:
            from scenes.cutscene import CutsceneScene
            self.mgr.switch(CutsceneScene, state=self.state, script_file="script_ch1.json", next_scene="concert")