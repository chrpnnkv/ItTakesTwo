# scenes/cutscene.py
import pygame as pg
from core.base_scene import BaseScene
from core.resources import img, font, load_json


def _resolve_scene(key):
    if key == "concert": from scenes.concert_game import ConcertGame; return ConcertGame
    if key == "balance": from scenes.balance_game import BalanceGame; return BalanceGame
    if key == "maze":    from scenes.maze_game import MazeGame; return MazeGame
    if key == "oracle":  from scenes.oracle_game import OracleGame; return OracleGame
    if key == "puhovik":
        from scenes.puhovik_game import PuhovikGame;
        return PuhovikGame

    if key == "birthday": from scenes.birthday_game import BirthdayGame; return BirthdayGame
    if key == "rain":    from scenes.rain_game import RainGame; return RainGame
    if key == "end":     from scenes.achievements_view import AchievementsView; return AchievementsView
    raise KeyError(key)


class CutsceneScene(BaseScene):
    """
    Поддерживает два типа слайдов:
      1) обычный: { "bg": "file.png", "text": "строка...", "fx": "fade" }
      2) диалог:  {
            "type": "dialog",
            "bg": "file.png",
            "speaker": "Имя",
            "portrait": "portraits/masha.png",   # assets/img/portraits/...
            "side": "left" | "right",
            "text": "реплика",
            "fx": "fade"
         }
    В JSON можно указать "next": "<scene_key>", это перекроет параметр next_scene.
    """

    def __init__(self, manager, state, script_file, next_scene):
        super().__init__(manager)
        self.state = state

        data = load_json(script_file)
        # обратная совместимость: раньше был просто {"slides":[...]}
        self.slides = data["slides"] if "slides" in data else data
        self.next_scene_key = data.get("next", next_scene)

        self.idx = 0
        self.alpha = 0  # для fade-in
        self._next_allowed = 0  # debounce клика
        self._w, self._h = self.screen.get_size()

        # шрифты
        self.font_text = font("better-vcr-5.2.ttf", 24)
        self.font_name = font("better-vcr-5.2.ttf", 20)

    # ---------- управление ----------
    def handle_event(self, e):
        if e.type in (pg.MOUSEBUTTONDOWN, pg.KEYDOWN):
            now = pg.time.get_ticks()
            if now < self._next_allowed:
                return
            self._next_allowed = now + 160  # 160 мс дебаунс

            self.idx += 1
            self.alpha = 0
            if self.idx >= len(self.slides):
                if self.next_scene_key == "ch2":
                    self.mgr.switch(
                        CutsceneScene,
                        state=self.state,
                        script_file="script_ch2.json",  # если лежит в data/ch2, см. ниже
                        next_scene="maze"  # дальше по твоему порядку
                    )
                    return
                if self.next_scene_key == "ch3":
                    self.mgr.switch(
                        CutsceneScene,
                        state=self.state,
                        script_file="script_ch3.json",  # если лежит в data/ch2, см. ниже
                        next_scene="rain"  # дальше по твоему порядку
                    )
                    return
                if self.next_scene_key == "ch4":
                    self.mgr.switch(
                        CutsceneScene,
                        state=self.state,
                        script_file="script_ch4.json",  # если лежит в data/ch2, см. ниже
                        next_scene="coat"  # дальше по твоему порядку
                    )
                    return
                next_cls = _resolve_scene(self.next_scene_key)
                self.mgr.switch(next_cls, state=self.state)

    # ---------- логика ----------
    def update(self, dt):
        # плавное появление
        self.alpha = min(255, self.alpha + int(400 * dt))

    # ---------- отрисовка ----------
    def draw(self):
        self.screen.fill((0, 0, 0))
        slide = self.slides[self.idx]

        # фон
        bg_name = slide.get("bg")
        if bg_name:
            bg = img(bg_name)
            self.screen.blit(pg.transform.scale(bg, (self._w, self._h)), (0, 0))

        # контент по типу
        if slide.get("type") == "dialog":
            self._draw_dialog(slide)
        else:
            self._draw_plain(slide)

        # эффект fade-in
        if slide.get("fx") == "fade":
            overlay = pg.Surface((self._w, self._h), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 255 - self.alpha))
            self.screen.blit(overlay, (0, 0))

    # ---------- виды слайдов ----------
    def _draw_plain(self, slide):
        text = slide.get("text", "")
        if not text:
            return
        panel_h = 96
        panel = pg.Surface((self._w, panel_h), pg.SRCALPHA)
        panel.fill((0, 0, 0, 150))
        self.screen.blit(panel, (0, self._h - panel_h))

        self._blit_wrapped(text, (28, self._h - panel_h + 18), self._w - 56)

    def _draw_dialog(self, slide):
        w, h = self._w, self._h
        panel_h = int(h * 0.17)
        panel_rect = pg.Rect(0, h - panel_h, w, panel_h)

        # --- PORTRET СЛЕВА, СЗАДИ ПАНЕЛИ ---
        portrait_name = slide.get("portrait")
        text_left = 34
        if portrait_name:
            p = img(portrait_name)
            target_h = int(panel_h * 4.5)  # крупнее панели
            target_w = int(p.get_width() * (target_h / p.get_height()))
            p = pg.transform.smoothscale(p, (target_w, target_h))
            x_portrait = 0  # всегда слева
            y_portrait = h - panel_h - int(target_h * 0.75)  # выступает вверх
            # рисуем ПЕРВЫМ, чтобы потом панель легла сверху
            self.screen.blit(p, (x_portrait, y_portrait))
            text_left = 34

        # --- ТЁМНАЯ ПАНЕЛЬ СНИЗУ (поверх части портрета) ---
        panel = pg.Surface(panel_rect.size, pg.SRCALPHA)
        panel.fill((0, 0, 0, 190))
        self.screen.blit(panel, panel_rect)

        # --- ИМЯ И ТЕКСТ ---
        speaker = slide.get("speaker")
        if speaker:
            name_surf = self.font_name.render(str(speaker), True, (200, 200, 220))
            self.screen.blit(name_surf, (text_left, panel_rect.y + 14))

        text = slide.get("text", "")
        self._blit_wrapped_colored(text, (text_left, panel_rect.y + 44),
                                   w - 28 - text_left, (230, 230, 230))

    # перенос строк по ширине
    def _blit_wrapped(self, text, pos, max_w):
        x, y = pos
        words = str(text).split()
        line = ""
        for w in words:
            test = (line + " " + w).strip()
            surf = self.font_text.render(test, True, (255, 255, 255))
            if surf.get_width() > max_w and line:
                self.screen.blit(self.font_text.render(line, True, (255, 255, 255)), (x, y))
                y += 28
                line = w
            else:
                line = test
        if line:
            self.screen.blit(self.font_text.render(line, True, (255, 255, 255)), (x, y))

    # Внутри класса CutsceneScene, ниже _draw_dialog / _draw_plain:

    def _blit_wrapped_colored(self, text, pos, max_w, color):
        """Рисует многострочный текст заданным цветом с переносами по ширине."""
        x, y = pos
        words = str(text).split()
        line = ""
        for w in words:
            test = (line + " " + w).strip()
            surf = self.font_text.render(test, True, color)
            if surf.get_width() > max_w and line:
                self.screen.blit(self.font_text.render(line, True, color), (x, y))
                y += int(self.font_text.get_height() * 1.05)
                line = w
            else:
                line = test
        if line:
            self.screen.blit(self.font_text.render(line, True, color), (x, y))
