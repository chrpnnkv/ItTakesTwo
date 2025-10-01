import pygame as pg
import math
from .resources import font, img, sfx
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class _IntroLine:
    text: str
    size: int
    color: Tuple[int,int,int]
    t0: float      # момент старта появления (сек от начала заставки)
    alpha: float = 0.0
    yofs: float = 20.0
    scale: float = 1.06

class MiniIntro:
    """
    Заставка для мини-игры с анимированным текстом.
    """

    def __init__(self,
                 lines: List[Tuple[str, int, Tuple[int,int,int]]],
                 bg_color: Tuple[int,int,int] | None = None,
                 auto_start_after: Optional[float] = None,
                 hint_text: str = "Нажми любую клавишу",
                 fade_in: float = 0.35,
                 line_gap: int = 16,
                 start_delay_step: float = 0.18,
                 bg_image: str | None = None):
        self.lines_raw = lines
        self.bg_color = bg_color
        self.auto_start_after = auto_start_after
        self.hint_text = hint_text
        self.fade_in = fade_in
        self.line_gap = line_gap
        self.start_delay_step = start_delay_step
        self.bg_image = None
        if bg_image:
            try:
                self.bg_image = pg.image.load(f"assets/img/{bg_image}").convert()
            except Exception:
                self.bg_image = None

        self.time = 0.0
        self.hide = False
        self.done = False
        self.hide_time = 0.0
        self.hide_dur = 0.30

        # подготовка строк
        self.font_cache: dict[int, pg.font.Font] = {}
        t0 = 0.0
        self.lines: List[_IntroLine] = []
        for text, size, color in self.lines_raw:
            self.lines.append(_IntroLine(text, size, color, t0))
            t0 += self.start_delay_step

        self.hint_alpha = 0.0

    def _font(self, size: int):
        if size not in self.font_cache:
            self.font_cache[size] = pg.font.Font("assets/fonts/better-vcr-5.2.ttf", size)
        return self.font_cache[size]

    def handle_event(self, e: pg.event.Event):
        if self.done:
            return
        if e.type in (pg.KEYDOWN, pg.MOUSEBUTTONDOWN):
            self.hide = True

    def update(self, dt: float):
        if self.done:
            return
        self.time += dt
        if self.auto_start_after is not None and not self.hide:
            if self.time >= self.auto_start_after:
                self.hide = True
        for L in self.lines:
            t_rel = max(0.0, self.time - L.t0)
            k = min(1.0, t_rel / max(0.001, self.fade_in))
            L.alpha = 255.0 * k
            L.yofs = 20.0 * (1.0 - k)
            L.scale = 1.06 - 0.06 * k
        self.hint_alpha = 200 + int(55 * (0.5 + 0.5 * math.sin(pg.time.get_ticks() * 0.006)))
        if self.hide:
            self.hide_time += dt
            if self.hide_time >= self.hide_dur:
                self.done = True

    def draw(self, screen: pg.Surface):
        if self.done:
            return
        # В draw() — перед затемнением и текстом:
        W, H = screen.get_size()

        # 1) Фон-картинка (если есть) — подгоняем по размеру экрана:
        if self.bg_image:
            bg = pg.transform.smoothscale(self.bg_image, (W, H))
            screen.blit(bg, (0, 0))
        elif self.bg_color:
            # fallback: однотонный фон
            screen.fill(self.bg_color)

        overlay = pg.Surface((W, H), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 40))
        screen.blit(overlay, (0, 0))

        total_h = 0
        for L in self.lines:
            f = self._font(L.size)
            rect = f.render(L.text, True, L.color).get_rect()
            total_h += rect.height
        total_h += self.line_gap * (len(self.lines) - 1)

        y = H // 2 - total_h // 2
        for L in self.lines:
            f = self._font(L.size)
            surf = f.render(L.text, True, L.color)
            if abs(L.scale - 1.0) > 0.001:
                sw = max(1, int(surf.get_width() * L.scale))
                sh = max(1, int(surf.get_height() * L.scale))
                surf = pg.transform.smoothscale(surf, (sw, sh))
            rect = surf.get_rect(centerx=W // 2)
            rect.top = int(y + L.yofs)
            if L.alpha < 255:
                s2 = surf.convert_alpha()
                s2.fill((255, 255, 255, int(L.alpha)), special_flags=pg.BLEND_RGBA_MULT)
                screen.blit(s2, rect.topleft)
            else:
                screen.blit(surf, rect.topleft)
            y = rect.bottom + self.line_gap

        hint_font = self._font(20)
        hint = hint_font.render(self.hint_text, True, (230, 230, 230))
        hint_rect = hint.get_rect(center=(W // 2, H - 60))
        hint_s = hint.convert_alpha()
        hint_s.fill((255, 255, 255, int(self.hint_alpha)), special_flags=pg.BLEND_RGBA_MULT)
        screen.blit(hint_s, hint_rect)

        if self.hide:
            k = min(1.0, self.hide_time / self.hide_dur)
            fade = pg.Surface((W, H), pg.SRCALPHA)
            fade.fill((0, 0, 0, int(255 * k)))
            screen.blit(fade, (0, 0))


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

def _ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3

class ToastManager:
    def __init__(self):
        self.items = []
        self.in_dur  = 0.30    # «выплыть» сверху
        self.out_dur = 0.30    # «уплыть» вверх
        self.pad = 10
        self.gap = 8
        # дефолтные ресурсы
        self._default_icon = None
        self._pop_sfx = None
        try:
            self._default_icon = img("trophy.png")        # assets/img/trophy.png
        except Exception:
            self._default_icon = None
        try:
            self._pop_sfx = sfx("achieve.wav")            # assets/sfx/achieve.wav
            self._pop_sfx.set_volume(0.75)
        except Exception:
            self._pop_sfx = None

    def push(self, text: str, ttl: float = 2.5, *, icon_name: str | None = None, play_sound: bool = True):
        surf = font("better-vcr-5.2.ttf", 22).render(text, True, (255,255,255))
        icon = None
        if icon_name:
            try:
                icon = img(icon_name)
            except Exception:
                icon = None
        if icon is None:
            icon = self._default_icon

        icon_w = icon.get_width() if icon else 0
        icon_gap = 8 if icon else 0

        tw, th = surf.get_size()
        w_total = self.pad*2 + icon_w + icon_gap + tw
        h_total = self.pad*2 + max(th, icon.get_height() if icon else th)

        item = {
            "text": text, "time": ttl, "ttl": ttl, "surf": surf,
            "size": (w_total, h_total), "icon": icon, "played": False,
        }
        self.items.append(item)

        if play_sound and self._pop_sfx:
            try:
                self._pop_sfx.play()
                item["played"] = True
            except Exception:
                pass

    def update(self, dt: float):
        for it in self.items:
            it["time"] -= dt
        self.items = [it for it in self.items if it["time"] > -self.out_dur]

    def draw(self, surface: pg.Surface):
        if not self.items:
            return

        sw, _ = surface.get_size()
        x_right = sw - 16
        y_top = 16

        # целевые позиции стека
        targets = []
        y = y_top
        for it in self.items:
            w, h = it["size"]
            r = pg.Rect(0, 0, w, h)
            r.top = y
            r.right = x_right
            targets.append(r)
            y += h + self.gap

        for it, rect in zip(self.items, targets):
            ttl, t = it["ttl"], it["time"]
            w, h = it["size"]

            # вход
            t_in = ttl - t
            slide_in_k = 1.0 if t_in >= self.in_dur else _ease_out_cubic(max(0.0, min(1.0, t_in / self.in_dur)))

            # выход
            fade_k = 1.0
            slide_out_k = 0.0
            if 0 <= t < self.out_dur:
                u = 1.0 - (t / self.out_dur)
                slide_out_k = _ease_out_cubic(u)
                fade_k = 1.0 - u
            elif t < 0:
                slide_out_k = 1.0
                fade_k = 0.0

            dy_in  = (1.0 - slide_in_k) * (h + self.gap)
            dy_out = slide_out_k * (h + self.gap)
            y_actual = rect.top - dy_in - dy_out

            # фон
            bg = pg.Surface((w, h), pg.SRCALPHA)
            bg.fill((20, 20, 28, int(220 * fade_k)))
            surface.blit(bg, (rect.left, y_actual))
            # рамка
            pg.draw.rect(surface, (180,180,200, int(255*fade_k)),
                         pg.Rect(rect.left, y_actual, w, h), 2, border_radius=8)

            # иконка + текст
            cx = rect.left + self.pad
            cy = y_actual + self.pad
            if it["icon"] is not None and fade_k > 0:
                icon = it["icon"]
                ih = min(h - self.pad*2, 24)
                iw = max(1, int(icon.get_width() * (ih / icon.get_height())))
                icon_draw = pg.transform.smoothscale(icon, (iw, ih))
                surface.blit(icon_draw, (cx, cy))
                cx += iw + 8
            if fade_k > 0:
                surface.blit(it["surf"], (cx, cy))


TOASTS = ToastManager()