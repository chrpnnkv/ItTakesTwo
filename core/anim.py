import os, glob
import pygame as pg
from core.resources import img

class AnimatedSprite:
    """
    Универсальная анимация из папки assets/img/character.
    Ожидается структура файлов по направлениям:
      left_0.png .. left_3.png
      right_0.png .. right_3.png
      up_0.png .. up_3.png
      down_0.png .. down_3.png
    Кол-во кадров может отличаться — берём все кадры по маске.
    """
    def __init__(self, base_dir="character", fps=10, scale=1.0):
        self.frames = {d: [] for d in ("left","right","forward","back")}
        root = os.path.join("assets", "img", base_dir)
        for d in self.frames:
            # собираем все кадры по направлению, сортируем по номеру
            files = sorted(glob.glob(os.path.join(root, f"{d}_*.png")))
            if not files:
                # запасной вариант: vl_{d}_*.png
                files = sorted(glob.glob(os.path.join(root, f"vl_{d}_*.png")))
            for f in files:
                surf = img(os.path.join(base_dir, os.path.basename(f)))
                if scale != 1.0:
                    w, h = surf.get_width(), surf.get_height()
                    surf = pg.transform.smoothscale(surf, (int(w*scale), int(h*scale)))
                self.frames[d].append(surf)

        # если какие-то наборы пустые — подменим ближайшими
        def fallback(dst, src):
            if not self.frames[dst] and self.frames[src]:
                self.frames[dst] = self.frames[src]
        fallback("left", "right"); fallback("right", "left")
        fallback("forward", "back");    fallback("back", "forward")

        self.fps = fps
        self.timer = 0.0
        self.index = 0
        self.direction = "forward"
        self.pos = pg.Vector2(0, 0)
        # хитбокс (центрируем по нижней точке)
        fr = self.frames[self.direction][0]
        self.offset = pg.Vector2(fr.get_width()//2, fr.get_height()-4)

    def set_direction(self, dir_name: str):
        if dir_name in self.frames and self.direction != dir_name:
            self.direction = dir_name
            self.index = 0
            self.timer = 0.0

    def update(self, dt: float, moving: bool):
        if moving:
            self.timer += dt
            if self.timer >= 1.0 / max(1, self.fps):
                self.timer = 0.0
                self.index = (self.index + 1) % len(self.frames[self.direction])
        else:
            self.index = 0
            self.timer = 0.0

    def draw(self, surface: pg.Surface):
        frame = self.frames[self.direction][self.index]
        draw_pos = (int(self.pos.x - self.offset.x), int(self.pos.y - self.offset.y))
        surface.blit(frame, draw_pos)

    def get_rect(self) -> pg.Rect:
        fr = self.frames[self.direction][self.index]
        return fr.get_rect(center=(int(self.pos.x), int(self.pos.y)-4))
