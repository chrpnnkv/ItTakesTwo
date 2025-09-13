import pygame as pg
from core.base_scene import BaseScene
from core.resources import img, font, load_json


def _resolve_scene(key):
    if key == "concert":
        from scenes.concert_game import ConcertGame
        return ConcertGame
    if key == "maze":
        from scenes.maze_game import MazeGame
        return MazeGame
    if key == "end":
        from scenes.achievements_view import AchievementsView
        return AchievementsView
    raise KeyError(f"Unknown next_scene: {key}")


class CutsceneScene(BaseScene):
    def __init__(self, manager, state, script_file, next_scene):
        super().__init__(manager)
        self.state = state
        self.data = load_json(script_file)["slides"]
        self.idx = 0
        self.alpha = 0
        self.next_scene_key = next_scene

    def handle_event(self, e):
        if e.type in (pg.MOUSEBUTTONDOWN, pg.KEYDOWN):
            self.idx += 1
            self.alpha = 0
            if self.idx >= len(self.data):
                next_cls = _resolve_scene(self.next_scene_key)
                self.mgr.switch(next_cls, state=self.state)

    def update(self, dt):
        self.alpha = min(255, self.alpha + int(400 * dt))

    def draw(self):
        self.screen.fill((0, 0, 0))
        slide = self.data[self.idx]
        bg = img(slide["bg"])
        self.screen.blit(pg.transform.scale(bg, self.screen.get_size()), (0, 0))
        label = font("better-vcr-5.2.ttf", 24).render(slide["text"], True, (255, 255, 255))
        self.screen.blit(label, (40, self.screen.get_height() - 80))

        if slide.get("fx") == "fade":
            overlay = pg.Surface(self.screen.get_size(), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 255 - self.alpha))
            self.screen.blit(overlay, (0, 0))