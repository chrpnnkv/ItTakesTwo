import pygame as pg
from .resources import font, img, sfx

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