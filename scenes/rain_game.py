# scenes/rain_game.py
from __future__ import annotations
import random
import pygame as pg
import math
from dataclasses import dataclass
from core.base_scene import BaseScene

RND = random.Random()

# --- геймплейные константы ---
HP_MAX              = 100
DMG_PER_HIT         = 28

COLS                = 6           # количество колонок
LANE_MARGIN_X       = 28          # отступ поля от краёв
LANE_TWEEN_SPEED    = 12.0        # скорость твина к центру колонки (чем больше — тем резче)

WARN_TIME           = 0.55        # длительность предупреждения
BASE_DROP_SPEED     = 720.0       # стартовая скорость падения (px/s)
SPEED_PER_MIN       = 220.0       # ускорение дождя в минуту
WAVE_INTERVAL       = 1.05        # стартовый интервал между волнами
WAVE_DELTA_PER_MIN  = -0.22       # как быстро сокращается интервал (в мин)
WAVE_INTERVAL_MIN   = 0.40
SURVIVE_TIME        = 25.0        # нужно выжить столько секунд

# зонт
UMBRELLA_ACTIVE     = 0.95        # держится зонт
UMBRELLA_COOLDOWN   = 1.10        # перезарядка
UMBRELLA_OPEN_TIME  = 0.10        # фаза открытия
UMBRELLA_CLOSE_TIME = 0.10        # фаза закрытия

# визуал
FLASH_FREQ          = 8.5         # мерцание предупреждения
SHAKE_ON_HIT        = 6           # пиксели
SHAKE_TIME          = 0.18        # сек


@dataclass
class Beam:
    col: int
    state: str  # "warn" | "fall" | "splash"
    t: float = 0.0
    y: float = 0.0


class RainGame(BaseScene):
    """
    Мини-игра «Дождь» (позиционирование + тайминг):
      - ←/→ или A/D: перемещение между колонками (с твином).
      - SPACE: зонт (активное время + кулдаун; есть анимация открытия/закрытия).
      - Телеграф, падение, всплеск. Экранный шейк при попадании.
      - Победа по времени, поражение при HP<=0.
    """

    def __init__(self, manager, state):
        super().__init__(manager)
        self.state = state

        self.w, self.h = self.screen.get_size()
        self.ground_y = self.h - 110

        # сетка колонок
        inner_w = self.w - LANE_MARGIN_X * 2
        self.col_w = inner_w // COLS
        self.col_x0 = (self.w - (self.col_w * COLS)) // 2

        # позиция игрока — колонка + плавный твин к центру
        self.lane = COLS // 2            # индекс колонки (0..COLS-1)
        self.x_center = self._lane_center_x(self.lane)
        self.player_w, self.player_h = 42, 42
        self.player_y = self.ground_y - self.player_h - 2

        # зонт
        self.um_time = 0.0
        self.um_cd = 0.0
        self.um_open = 0.0
        self.um_closing = False

        # состояние
        self.hp = HP_MAX
        self.time_alive = 0.0
        self.time_since_wave = 0.0
        self.drop_speed = BASE_DROP_SPEED
        self.wave_interval = WAVE_INTERVAL

        # лучи
        self.beams: list[Beam] = []

        # эффекты
        self.shake_t = 0.0

        # вступительная заставка (если есть)
        try:
            from core.ui import MiniIntro
            self.intro = MiniIntro([
                ("МИНИ-ИГРА", 40, (235,235,240)),
                ("Дождь",      32, (255,230,150)),
                ("A/D или ←/→ — перемещение; SPACE — зонт", 22, (220,220,230)),
            ])
        except Exception:
            self.intro = None

    # ---------- утилиты ----------
    def _lane_center_x(self, lane: int) -> int:
        x = self.col_x0 + lane * self.col_w + self.col_w // 2
        return x

    def _player_rect(self) -> pg.Rect:
        return pg.Rect(int(self.x_center - self.player_w//2),
                       int(self.player_y),
                       self.player_w, self.player_h)

    # ---------- события ----------
    def handle_event(self, e):
        if self.intro and not self.intro.done:
            self.intro.handle_event(e)
            return

        if e.type == pg.KEYDOWN:
            if e.key in (pg.K_a, pg.K_LEFT):
                self.lane = max(0, self.lane - 1)
            elif e.key in (pg.K_d, pg.K_RIGHT):
                self.lane = min(COLS - 1, self.lane + 1)
            elif e.key == pg.K_SPACE:
                self._try_open_umbrella()

    def _try_open_umbrella(self):
        if self.um_time <= 0 and self.um_cd <= 0:
            self.um_time = UMBRELLA_ACTIVE
            self.um_closing = False
            self.um_open = 0.0001  # старт анимации

    # ---------- апдейт ----------
    def update(self, dt: float):
        if self.intro and not self.intro.done:
            self.intro.update(dt)
            return

        # твин игрока к центру целевой колонки (гладко)
        target_x = self._lane_center_x(self.lane)
        self.x_center += (target_x - self.x_center) * min(1.0, LANE_TWEEN_SPEED * dt)

        # зонт — фазы
        if self.um_time > 0:
            if self.um_open < 1.0 and not self.um_closing:
                self.um_open = min(1.0, self.um_open + dt / UMBRELLA_OPEN_TIME)
            self.um_time = max(0.0, self.um_time - dt)
            if self.um_time == 0.0:
                self.um_closing = True
        elif self.um_closing:
            self.um_open = max(0.0, self.um_open - dt / UMBRELLA_CLOSE_TIME)
            if self.um_open == 0.0:
                self.um_closing = False
                self.um_cd = UMBRELLA_COOLDOWN
        elif self.um_cd > 0:
            self.um_cd = max(0.0, self.um_cd - dt)

        # сложность
        self.time_alive += dt
        self.time_since_wave += dt
        self.drop_speed = BASE_DROP_SPEED + SPEED_PER_MIN * (self.time_alive / 60.0)
        self.wave_interval = max(WAVE_INTERVAL_MIN, WAVE_INTERVAL + WAVE_DELTA_PER_MIN * (self.time_alive / 60.0))

        # волны
        if self.time_since_wave >= self.wave_interval:
            self.time_since_wave = 0.0
            self._spawn_wave()

        self._update_beams(dt)

        # шейк
        if self.shake_t > 0:
            self.shake_t = max(0.0, self.shake_t - dt)

        # победа
        if self.time_alive >= SURVIVE_TIME:
            self._win()

    def _spawn_wave(self):
        # чаще 2, иногда 1 или 3
        count = RND.choice((1, 2, 2, 3))
        cols = RND.sample(range(COLS), count)
        for c in cols:
            self.beams.append(Beam(col=c, state="warn"))

        # иногда «ловушка» — почти все колонки, кроме одной
        # (редко, чтобы не бесить)
        if RND.random() < 0.08 and COLS >= 5:
            safe = RND.randrange(COLS)
            self.beams = [Beam(col=i, state="warn") for i in range(COLS) if i != safe]

    def _update_beams(self, dt: float):
        to_remove = []
        for i, b in enumerate(self.beams):
            if b.state == "warn":
                b.t += dt
                if b.t >= WARN_TIME:
                    b.state = "fall"; b.t = 0.0; b.y = 0.0
            elif b.state == "fall":
                b.y += self.drop_speed * dt
                if b.y >= self._drop_h():
                    self._resolve_hit(b)
                    b.state = "splash"; b.t = 0.0
            elif b.state == "splash":
                b.t += dt
                if b.t >= 0.22:
                    to_remove.append(i)
        for idx in reversed(to_remove):
            self.beams.pop(idx)

    def _drop_h(self) -> int:
        return self.ground_y

    def _resolve_hit(self, b: Beam):
        # попадание: если колонка бьёт ту же, где игрок,
        # и зонт НЕ полностью открыт и активен.
        player_lane = self._lane_by_x(self.x_center)
        umbrella_ok = (self.um_open >= 0.999 and self.um_time > 0.0)
        if b.col == player_lane and not umbrella_ok:
            self.hp = max(0, self.hp - DMG_PER_HIT)
            self.shake_t = SHAKE_TIME
            if self.hp <= 0:
                self._lose()

    def _lane_by_x(self, cx: float) -> int:
        # ближайшая колонка к центру игрока
        rel = int((cx - self.col_x0) // self.col_w)
        return max(0, min(COLS - 1, rel))

    # ---------- исходы ----------
    def _win(self):
        try:
            from core.ui import TOASTS
            TOASTS.push("Ачивка: Лягушонок", icon_name="trophy.png", ttl=2.7)
        except Exception:
            pass
        self.state.award("lyagushka")
        self.state.save()
        from scenes.cutscene import CutsceneScene
        self.mgr.switch(CutsceneScene, state=self.state,
                        script_file="script_ch3_moving.json", next_scene="end")

    def _lose(self):
        from scenes.cutscene import CutsceneScene
        self.mgr.switch(CutsceneScene, state=self.state,
                        script_file="script_ch3_rain_retry.json", next_scene="rain")

    # ---------- отрисовка ----------
    def draw(self):
        ox = oy = 0
        if self.shake_t > 0.0:
            k = self.shake_t / SHAKE_TIME
            amp = int(SHAKE_ON_HIT * k)
            ox = RND.randint(-amp, amp)
            oy = RND.randint(-amp, amp)

        surf = self.screen
        surf.fill((18, 18, 26))

        # небо/земля
        pg.draw.rect(surf, (22, 24, 36), (ox, oy, self.w, self.ground_y))
        pg.draw.rect(surf, (26, 32, 32), (ox, oy + self.ground_y, self.w, self.h - self.ground_y))

        # делители колонок
        for i in range(1, COLS):
            x = self.col_x0 + i * self.col_w + ox
            pg.draw.line(surf, (30, 36, 52), (x, 0 + oy), (x, self.ground_y + oy), 1)

        # лучи
        for b in self.beams:
            x = self.col_x0 + b.col * self.col_w + ox
            if b.state == "warn":
                blink = 0.5 + 0.5 * math.sin(pg.time.get_ticks() * 0.001 * 2 * 3.14159 * FLASH_FREQ)
                color = (120 + int(60*blink), 170 + int(50*blink), 255)
                r = pg.Rect(x + 6, 8 + oy, self.col_w - 12, 10)
                pg.draw.rect(surf, color, r, border_radius=3)
            elif b.state == "fall":
                top = 0 + oy
                bottom = min(int(b.y) + oy, self.ground_y + oy)
                cx = x + self.col_w // 2
                core = pg.Rect(cx - 3, top, 6, bottom - top)
                side1 = pg.Rect(cx - 5, top, 2, bottom - top)
                side2 = pg.Rect(cx + 3, top, 2, bottom - top)
                pg.draw.rect(surf, (130, 180, 255), core, border_radius=3)
                pg.draw.rect(surf, (100, 150, 220), side1)
                pg.draw.rect(surf, (100, 150, 220), side2)
            elif b.state == "splash":
                y = self.ground_y + oy
                pg.draw.line(surf, (160, 200, 255), (x + 10, y), (x + self.col_w - 10, y), 2)

        # игрок
        prect = self._player_rect().move(ox, oy)
        pg.draw.rect(surf, (215, 215, 232), prect, border_radius=6)

        # зонт — полудиск с анимацией
        if self.um_open > 0.0:
            cx = prect.centerx
            cy = prect.top + 6
            radius = int(44 * self.um_open)
            pg.draw.circle(surf, (120, 200, 160), (cx, cy), radius)
            pg.draw.rect(surf, (18, 18, 26), (cx - radius, cy, radius * 2, radius))

        # HUD
        self._draw_hud(surf)

        # интро
        if self.intro and not self.intro.done:
            self.intro.draw(surf)

    def _draw_hud(self, surf: pg.Surface):
        # HP
        pg.draw.rect(surf, (50, 58, 66), (20, 18, 300, 16), border_radius=4)
        w_hp = int(300 * (self.hp / HP_MAX))
        pg.draw.rect(surf, (120, 220, 140), (20, 18, w_hp, 16), border_radius=4)

        # зонт (актив/кд)
        bar_x, bar_y, bar_w, bar_h = 20, 40, 160, 8
        pg.draw.rect(surf, (46, 50, 56), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        if self.um_time > 0:
            k = self.um_time / UMBRELLA_ACTIVE
            pg.draw.rect(surf, (140, 220, 200), (bar_x, bar_y, int(bar_w * k), bar_h), border_radius=3)
        elif self.um_cd > 0:
            k = 1.0 - (self.um_cd / UMBRELLA_COOLDOWN)
            pg.draw.rect(surf, (90, 120, 110), (bar_x, bar_y, int(bar_w * k), bar_h), border_radius=3)

        # таймер
        remain = max(0.0, SURVIVE_TIME - self.time_alive)
        txt = pg.font.SysFont(None, 22).render(f"Осталось: {remain:0.1f}с", True, (220, 220, 230))
        surf.blit(txt, (20, 56))
