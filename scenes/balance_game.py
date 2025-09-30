# scenes/balance_game.py
import pygame as pg
from core.base_scene import BaseScene

GRAVITY = 1200


class BalanceGame(BaseScene):
    def __init__(self, manager, state):
        super().__init__(manager)
        self.state = state
        w, h = self.screen.get_size()

        # базовая геометрия
        self.base_w = 120  # стартовая ширина
        self.y_base = h - 80  # Y нижней платформы
        self.current_top_y = self.y_base  # текущая "вершина" башни

        # диапазоны случайностей
        self.min_h, self.max_h = 16, 34  # толщина слоя (px) — будет разной
        self.min_gap, self.max_gap = 4, 16  # зазор между слоями (px)

        # верхний шаблон (начальный) — по центру
        cx = w // 2
        self.curr_w = self.base_w
        self.slot_xleft = cx - self.curr_w // 2

        # уложенные реальные слои
        self.blocks: list[pg.Rect] = []

        # падающий блок / каретка
        self.drop_speed = 230
        self.drop_y = 80

        # контейнер для падающих "обрезков" (визуальный эффект)
        self.fragments: list[tuple[pg.Rect, float]] = []

        # цель по количеству уложенных слоёв
        self.goal = 8
        self.ended = False

        # подготовим первый слот и активный блок
        self._prepare_next_slot()
        self._spawn_active()

    # ---------- helpers ----------
    def _prepare_next_slot(self):
        """Случайные толщина и зазор для следующего слоёвого 'слота'."""
        next_h = pg.math.clamp(self.min_h, self.max_h, self.min_h)  # заглушка для mypy
        next_gap = pg.math.clamp(self.min_gap, self.max_gap, self.min_gap)
        # реально выбираем случайности
        next_h = self.min_h + (pg.time.get_ticks() % (self.max_h - self.min_h + 1))
        next_gap = self.min_gap + (pg.time.get_ticks() // 7 % (self.max_gap - self.min_gap + 1))
        # верхняя грань будущего слоя:
        top = self.current_top_y - next_gap - next_h
        self.slot_rect = pg.Rect(self.slot_xleft, top, self.curr_w, next_h)

    def _spawn_active(self):
        """Создать движущийся блок шириной = текущей ширине шаблона."""
        self.block_w = self.curr_w
        self.falling = False
        self.vy = 0.0
        self.dir = 1
        self.x = 40
        self.active = pg.Rect(self.x, self.drop_y, self.block_w, self.slot_rect.height)

    # ---------- события ----------
    def handle_event(self, e):
        if e.type == pg.KEYDOWN and e.key == pg.K_SPACE and not self.falling and not self.ended:
            self.falling = True
            self.vy = 0.0

    # ---------- цикл ----------
    def update(self, dt):
        if self.ended:
            return

        W, H = self.screen.get_size()

        if not self.falling:
            # движение каретки слева-направо
            left = 40
            right = W - 40 - self.active.width
            self.x += self.drop_speed * self.dir * dt
            if self.x < left:
                self.x = left;
                self.dir = 1
            if self.x > right:
                self.x = right;
                self.dir = -1
            self.active.topleft = (int(self.x), self.active.top)
        else:
            # падение
            self.vy += GRAVITY * dt
            self.active.y += int(self.vy * dt)

            # посадка при достижении низа слота
            if self.active.bottom >= self.slot_rect.bottom:
                placed = self.active.clip(self.slot_rect)

                # слишком узкий остаток — промах → кат-сцена-ретрай
                min_width = max(8, self.slot_rect.height // 2)
                if placed.width < min_width or placed.height <= 0:
                    self.fragments.append([self.active.copy(), self.vy])
                    from scenes.cutscene import CutsceneScene
                    self.mgr.switch(CutsceneScene, state=self.state,
                                    script_file="script_ch1_balance_retry.json",
                                    next_scene="balance")
                    return

                # обрезки (лево/право) уроним визуально
                if self.active.left < self.slot_rect.left:
                    left_part = pg.Rect(self.active.left, self.slot_rect.top,
                                        self.slot_rect.left - self.active.left, self.slot_rect.height)
                    if left_part.width > 0:
                        self.fragments.append([left_part, self.vy])
                if self.active.right > self.slot_rect.right:
                    right_part = pg.Rect(self.slot_rect.right, self.slot_rect.top,
                                         self.active.right - self.slot_rect.right, self.slot_rect.height)
                    if right_part.width > 0:
                        self.fragments.append([right_part, self.vy])

                # кладём только пересечение
                self.blocks.append(placed)

                # обновляем вершину и шаблон для следующего слоя
                self.current_top_y = self.slot_rect.top
                self.curr_w = placed.width
                self.slot_xleft = placed.left

                # победа?
                if len(self.blocks) >= self.goal:
                    from core.ui import TOASTS
                    TOASTS.push("Ачивка: Скульптура из мусора", icon_name="trophy.png", ttl=2.8)
                    self.state.award("skulptura")
                    self.state.save()
                    from scenes.cutscene import CutsceneScene
                    self.mgr.switch(CutsceneScene, state=self.state,
                                    script_file="ch1/script_ch1_end.json", next_scene="end1")
                    return

                # готовим следующий слот (новые случайные толщина и зазор) и активный блок
                self._prepare_next_slot()
                self._spawn_active()

        # падение обрезков
        for frag in self.fragments:
            rect, vy = frag
            vy += GRAVITY * dt
            rect.y += int(vy * dt)
            frag[1] = vy
        # чистим, что улетело
        self.fragments = [f for f in self.fragments if f[0].top < H + 200]

    def draw(self):
        w, h = self.screen.get_size()
        self.screen.fill((18, 12, 20))

        # база
        cx = w // 2
        pg.draw.rect(self.screen, (60, 60, 80),
                     (cx - self.base_w // 2, self.y_base, self.base_w, 10), border_radius=3)

        # уложенные слои (разные толщины, с зазорами — т.к. мы храним реальные Rect)
        for r in self.blocks:
            pg.draw.rect(self.screen, (200, 160, 90), r, border_radius=4)

        # активный блок
        if not self.ended:
            pg.draw.rect(self.screen, (220, 190, 110), self.active, border_radius=4)

        # падающие обрезки
        for rect, _vy in self.fragments:
            pg.draw.rect(self.screen, (150, 120, 70), rect, border_radius=4)

        # подсказка
        tip = pg.font.SysFont(None, 22).render(
            "SPACE — сбросить. Блоки разной толщины и с зазорами. Собери 8 слоёв.",
            True, (210, 210, 210))
        self.screen.blit(tip, (16, 12))
