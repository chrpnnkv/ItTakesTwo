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
        if self.check_achievements():
            self.buttons = [
                Button((cx - 120, 180, 240, 48), "Начать", lambda: self.mgr.switch(
                    CutsceneScene, state=self.state, script_file="script_ch1.json", next_scene="concert")),
                Button((cx - 120, 240, 240, 48), "Продолжить", self._resume),
                Button((cx - 120, 300, 240, 48), "Ачивки", lambda: self.mgr.switch(AchievementsView, state=self.state)),
                Button((cx - 120, 360, 240, 48), "Выход", lambda: pg.event.post(pg.event.Event(pg.QUIT)))
            ]
        else:
            self.buttons = [
                Button((cx - 120, 180, 240, 48), "Начать", lambda: self.mgr.switch(
                    CutsceneScene, state=self.state, script_file="script_ch1.json", next_scene="concert")),
                Button((cx - 120, 260, 240, 48), "Ачивки", lambda: self.mgr.switch(AchievementsView, state=self.state)),
                Button((cx - 120, 340, 240, 48), "Выход", lambda: pg.event.post(pg.event.Event(pg.QUIT)))
            ]

    def handle_event(self, e):
        for b in self.buttons: b.handle_event(e)

    def draw(self):
        self.screen.fill((12,12,16))
        for b in self.buttons: b.draw(self.screen)

    def check_achievements(self):
        self.state.load()
        return len(self.state.achievements) > 0

    def _resume(self):
        from scenes.cutscene import CutsceneScene
        try:
            self.state.load()
        except Exception:
            # сейва нет/битый — начать с пролога → концерт
            self.mgr.switch(CutsceneScene, state=self.state,
                            script_file="script_ch1.json", next_scene="concert")
            return

        ach = set(self.state.achievements)

        if "da_ya_zhestkii" not in ach:
            # ещё не пройден «Концерт»
            self.mgr.switch(CutsceneScene, state=self.state,
                            script_file="script_ch1.json", next_scene="concert")
            return

        if "skulptura" not in ach:
            # концерт пройден, но «Баланс» ещё нет → кат-сцена «Дурак» → Balance
            self.mgr.switch(CutsceneScene, state=self.state,
                            script_file="script_ch1_durak.json", next_scene="balance")
            return

        if "stertye_nogi" not in ach:
            # после «Баланс» идём в лабиринт (вторая часть)
            self.mgr.switch(CutsceneScene, state=self.state,
                            script_file="script_ch2.json", next_scene="maze")
            return
        if "n" not in ach:
            # после «Баланс» идём в лабиринт (вторая часть)
            self.mgr.switch(CutsceneScene, state=self.state,
                            script_file="script_ch2.json", next_scene="birthday")
            return

        # всё пройдено — показываем ачивки / финал главы
        from scenes.achievements_view import AchievementsView
        self.mgr.switch(AchievementsView, state=self.state)
