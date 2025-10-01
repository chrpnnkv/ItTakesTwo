# scenes/puhovik_game.py
from __future__ import annotations
import random
import pygame as pg
from dataclasses import dataclass
from core.base_scene import BaseScene

RND = random.Random()

# --- параметры геймплея (правь как удобно) ---
TRACK_WIDTH_PAD     = 40        # поля слева/справа
AUTO_RUN_SPEED      = 130.0     # авто-движение вперёд (px/s)
SIDE_SPEED          = 280.0     # скорость смещения влево/вправо
ACCEL_PER_MIN       = 60.0      # ускорение авто-бега в минуту
SCROLL_BG_SPEED_K   = 0.65      # доля от AUTO_RUN_SPEED для параллакса фона

DIST_TO_GOAL        = 1800.0    # дистанция до финиша (px по миру)
OB_SPAWN_EVERY      = 0.65      # интервал спавна «потоков людей» (сек)
OB_SPEED_MIN        = 120.0     # горизонтальная скорость людей
OB_SPEED_MAX        = 260.0
OB_WIDTH_RANGE      = (36, 64)  # «ширина человека»
OB_LANE_H           = 58        # расстояние между «дорожками» (по Y)
OB_ROWS_AHEAD       = 12        # сколько рядов держим «в трубе» перед игроком
HIT_GRACE           = 4         # прощаем небольшое касание

HARD_CHANCE_PER_MIN = 0.25      # как часто добавлять «двойные» потоки

ACHIEVEMENT_KEY     = "zato_shubka_est"   # ключ ачивки «Зато шубка есть»

@dataclass
class Crowd:
    """Горизонтальный поток людей на фиксированной «дорожке» (y в мировых координатах)."""
    y: float
    dir: int              # -1 влево, +1 вправо
    speed: float          # px/s (модуля)
    gaps: list[pg.Rect]   # прямоугольники-люди в локальных координатах (x0..x1, y=0)
    width: int            # ширина всего коридора (в пикселях)

class PuhovikGame(BaseScene):
    """
    Мини-игра «Пуховик».
      — Персонаж бежит вперёд автоматически.
      — Навстречу идут «потоки людей» по горизонтали, их нужно обходить.
      — Столкнулся — проигрыш (retry-катсцена).
      — Добежал до финиша — победа, ачивка «Зато шубка есть».
    Управление: A/D или ←/→ — влево/вправо.
    """

    def __init__(self, manager, state):
        super().__init__(manager)
        self.state = state
        self.W, self.H = self.screen.get_size()

        # Игровая «дорожка»
        self.left = TRACK_WIDTH_PAD
        self.right = self.W - TRACK_WIDTH_PAD

        # Игрок
        self.player_w, self.player_h = 40, 52
        self.player_x = self.W // 2
        self.player_y = self.H - 120   # нижняя треть экрана
        self.world_y = 0.0             # пройденная дистанция (мировая координата по оси Y)

        # Скорости/сложность
        self.auto_speed = AUTO_RUN_SPEED
        self.spawn_timer = 0.0
        self.next_row_y = -OB_LANE_H   # ближайшая «дорожка» сверху (мировая Y)

        # Потоки людей
        self.streams: list[Crowd] = []

        # Эффекты
        self.shake_t = 0.0
        self.shake_amp = 6
        self.dead = False

        # Заставка
        try:
            from core.ui import MiniIntro
            self.intro = MiniIntro([
                ("МИНИ-ИГРА", 40, (235,235,240)),
                ("Пуховик",    32, (255,230,150)),
                ("A/D или ←/→ — уклоняйся от людей и догони героиню", 22, (220,220,230)),
            ])
        except Exception:
            self.intro = None

    # ------------- Вспомогательные -------------
    def _player_rect(self) -> pg.Rect:
        return pg.Rect(int(self.player_x - self.player_w//2),
                       int(self.player_y - self.player_h//2),
                       self.player_w, self.player_h)

    def _spawn_crowd_row(self, y: float, hard: bool = False):
        """Создаёт один или два потокa на мировой «дорожке» y."""
        width = self.right - self.left
        def make_stream(dir_sign: int) -> Crowd:
            speed = RND.uniform(OB_SPEED_MIN, OB_SPEED_MAX)
            # формы «людей» – набор прямоугольников через интервал
            gaps: list[pg.Rect] = []
            x = 0
            while x < width:
                w = RND.randint(*OB_WIDTH_RANGE)
                gaps.append(pg.Rect(x, 0, w, 40))
                x += w + RND.randint(18, 46)
            return Crowd(y=y, dir=dir_sign, speed=speed, gaps=gaps, width=width)

        if hard:
            # двойной поток: слева->право и справа->лево
            self.streams.append(make_stream(+1))
            self.streams.append(make_stream(-1))
        else:
            self.streams.append(make_stream(RND.choice((-1, +1))))

    def _maybe_spawn_rows_ahead(self):
        """Гарантирует «трубу» из нескольких рядов впереди игрока."""
        ahead_limit = self.world_y - OB_LANE_H * OB_ROWS_AHEAD
        while self.next_row_y > ahead_limit:
            hard = RND.random() < (HARD_CHANCE_PER_MIN * (self.world_y / (60.0 * self.auto_speed)))
            self._spawn_crowd_row(self.next_row_y, hard=hard)
            self.next_row_y -= OB_LANE_H

    # ------------- События -------------
    def handle_event(self, e):
        if self.intro and not self.intro.done:
            self.intro.handle_event(e)
            return

    # ------------- Апдейт -------------
    def update(self, dt: float):
        if self.intro and not self.intro.done:
            self.intro.update(dt)
            return
        if self.dead:
            return

        keys = pg.key.get_pressed()
        side = (keys[pg.K_d] or keys[pg.K_RIGHT]) - (keys[pg.K_a] or keys[pg.K_LEFT])
        self.player_x += side * SIDE_SPEED * dt
        self.player_x = max(self.left + self.player_w//2, min(self.right - self.player_w//2, self.player_x))

        # ускорение авто-бега со временем
        self.auto_speed = AUTO_RUN_SPEED + ACCEL_PER_MIN * (self.world_y / (60.0 * AUTO_RUN_SPEED))

        # двигаем мир «вниз» (игрок как бы бежит вперёд)
        self.world_y += self.auto_speed * dt

        # гарантируем ряды впереди
        self._maybe_spawn_rows_ahead()

        # апдейт потоков: их мировая Y сдвигается вниз вместе с камерой
        cam_offset = self.world_y  # сколько «прокрутили» мира
        prect = self._player_rect()

        collide = False
        for s in self.streams:
            # экранная Y = (мировая y + смещение камеры) + базовая высота
            screen_y = (s.y + cam_offset) + self.H * 0.18
            # горизонтальный сдвиг всего ряда (бесконечный зацикленный бегун)
            shift = (pg.time.get_ticks() * 0.001 * s.speed * s.dir) % (s.width + 120)
            base_x = self.left - 60 - shift if s.dir > 0 else self.left - 60 + shift

            # проверка столкновений с «людьми» ряда
            for r in s.gaps:
                rr = pg.Rect(int(base_x + r.x), int(screen_y - 20), r.w, r.h)
                # сам «человек» — это прямоугольник; можно немного «скруглить»:
                inflated = rr.inflate(-HIT_GRACE, -HIT_GRACE)
                if inflated.colliderect(prect):
                    collide = True
                    break
            if collide:
                break

        if collide:
            self._lose()
            return

        # Победа по дистанции
        if self.world_y >= DIST_TO_GOAL:
            self._win()
            return

        # Шейк (короткий)
        if self.shake_t > 0:
            self.shake_t = max(0.0, self.shake_t - dt)

    # ------------- Исходы -------------
    def _win(self):
        # Ачивка
        try:
            from core.ui import TOASTS
            TOASTS.push("Ачивка: Зато шубка есть", icon_name="trophy.png", ttl=2.6)
        except Exception:
            pass
        self.state.award("puhovik")
        self.state.save()
        # Переход: кат-сцена к «Третьяковке»
        from scenes.cutscene import CutsceneScene
        self.mgr.switch(CutsceneScene, state=self.state,
                        script_file="script_ch4_tretyakovka.json", next_scene="tretyakovka")

    def _lose(self):
        self.dead = True
        from scenes.cutscene import CutsceneScene
        self.mgr.switch(CutsceneScene, state=self.state,
                        script_file="script_ch4_puhovik_retry.json", next_scene="puhovik")

    # ------------- Отрисовка -------------
    def draw(self):
        surf = self.screen
        surf.fill((18, 18, 24))

        # параллакс-фон: бегущая «дорожка»
        scroll = int((self.world_y * SCROLL_BG_SPEED_K) % 40)
        for y in range(-scroll, self.H, 40):
            pg.draw.rect(surf, (22, 22, 30), (0, y, self.W, 20))

        # края «торгового центра»
        pg.draw.rect(surf, (34, 34, 46), (0, 0, self.left, self.H))
        pg.draw.rect(surf, (34, 34, 46), (self.right, 0, self.W - self.right, self.H))
        pg.draw.rect(surf, (44, 44, 58), (self.left, 0, self.right - self.left, self.H), 2)

        # потоки людей (как капсулы)
        cam_offset = self.world_y
        for s in self.streams:
            screen_y = (s.y + cam_offset) + self.H * 0.18
            shift = (pg.time.get_ticks() * 0.001 * s.speed * s.dir) % (s.width + 120)
            base_x = self.left - 60 - shift if s.dir > 0 else self.left - 60 + shift
            for r in s.gaps:
                rr = pg.Rect(int(base_x + r.x), int(screen_y - 20), r.w, r.h)
                pg.draw.rect(surf, (170, 70, 70), rr, border_radius=8)

        # игрок
        prect = self._player_rect()
        pg.draw.rect(surf, (220, 220, 240), prect, border_radius=8)

        # прогресс
        bar_w = 360
        pg.draw.rect(surf, (50, 58, 66), (20, 18, bar_w, 16), border_radius=4)
        k = max(0.0, min(1.0, self.world_y / DIST_TO_GOAL))
        pg.draw.rect(surf, (120, 220, 140), (20, 18, int(bar_w * k), 16), border_radius=4)
        txt = pg.font.SysFont(None, 22).render("Догони героиню", True, (220, 220, 230))
        surf.blit(txt, (20, 40))

        # интро-заставка
        if self.intro and not self.intro.done:
            self.intro.draw(surf)
