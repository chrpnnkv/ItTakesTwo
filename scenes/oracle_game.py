# scenes/oracle_game.py
import random
import pygame as pg
from core.base_scene import BaseScene

RND = random.Random()

class OracleGame(BaseScene):
    """
    Мини-игра «Оракул» (Space Invaders):
    - Игрок внизу двигается влево/вправо, стреляет наверх (SPACE).
    - Ряды врагов движутся горизонтально, от стен отскакивают и опускаются.
    - Враги иногда стреляют вниз.
    - Победа: все враги уничтожены → ачивка + кат-сцена.
    - Поражение: враги добрались до низа / попали в игрока → retry-кат-сцена.
    """

    # --- параметры геймплея (можно вынести в JSON при желании) ---
    PLAYER_SPEED = 280.0
    PLAYER_COOLDOWN = 0.28
    PLAYER_LIVES = 3

    BULLET_SPEED = 520.0
    ENEMY_BULLET_SPEED = 240.0

    ENEMY_ROWS = 5
    ENEMY_COLS = 10
    ENEMY_HSP = 70.0      # базовая горизонтальная скорость врагов
    ENEMY_Y_STEP = 20     # шаг опускания при смене направления
    ENEMY_FIRE_COOLDOWN = (0.7, 1.8)  # случайный интервал между выстрелами врагов

    SHIELD_COUNT = 0      # если захочешь щиты — сделаем

    def __init__(self, manager, state):
        super().__init__(manager)
        self.state = state

        w, h = self.screen.get_size()

        # Игрок
        self.player = pg.Rect(w//2 - 18, h - 64, 36, 16)
        self.player_cooldown = 0.0
        self.lives = self.PLAYER_LIVES
        self.score = 0

        # Пули
        self.bullets = []         # list[pg.Rect] — вверх
        self.enemy_bullets = []   # вниз

        # Враги — сетка прямоугольников
        self.enemies = []
        margin_x, margin_y = 80, 80
        spacing_x, spacing_y = 48, 36
        for r in range(self.ENEMY_ROWS):
            row = []
            for c in range(self.ENEMY_COLS):
                x = margin_x + c * spacing_x
                y = margin_y + r * spacing_y
                row.append(pg.Rect(x, y, 28, 18))
            self.enemies.append(row)

        self.enemy_dir = 1      # 1 вправо, -1 влево
        self.enemy_speed = self.ENEMY_HSP
        self.enemy_fire_timer = self._rand_enemy_fire_time()

        # Вступительная заставка (если подключила MiniIntro)
        try:
            from core.ui import MiniIntro
            self.intro = MiniIntro([
                ("МИНИ-ИГРА", 40, (235,235,240)),
                ("Оракул",    32, (255,230,150)),
                ("Стреляй по рядам, уворачивайся от ответного огня", 22, (220,220,230)),
            ])
        except Exception:
            self.intro = None

    # ------------- helpers -------------
    def _rand_enemy_fire_time(self):
        a, b = self.ENEMY_FIRE_COOLDOWN
        return RND.uniform(a, b)

    def _all_enemies(self):
        for row in self.enemies:
            for e in row:
                if e:  # Rect или None
                    yield e

    def _enemies_rect_bounds(self):
        # прямоугольник, ограничивающий всех живых врагов
        living = [e for e in self._all_enemies()]
        if not living:
            return None
        left = min(e.left for e in living)
        right = max(e.right for e in living)
        top = min(e.top for e in living)
        bottom = max(e.bottom for e in living)
        return pg.Rect(left, top, right-left, bottom-top)

    # ------------- events -------------
    def handle_event(self, e):
        # заставка может перехватывать
        if self.intro and not self.intro.done:
            self.intro.handle_event(e)
            return

        if e.type == pg.KEYDOWN and e.key == pg.K_SPACE and self.player_cooldown <= 0:
            # выстрел игрока
            self.player_cooldown = self.PLAYER_COOLDOWN
            b = pg.Rect(self.player.centerx - 2, self.player.top - 10, 4, 10)
            self.bullets.append(b)

    # ------------- update -------------
    def update(self, dt):
        # заставка активна — не начинаем игру
        if self.intro and not self.intro.done:
            self.intro.update(dt)
            return

        w, h = self.screen.get_size()
        keys = pg.key.get_pressed()

        # Движение игрока
        vx = (keys[pg.K_d] or keys[pg.K_RIGHT]) - (keys[pg.K_a] or keys[pg.K_LEFT])
        self.player.x += int(vx * self.PLAYER_SPEED * dt)
        self.player.clamp_ip(pg.Rect(8, 0, w-16, h))

        # Кулдаун стрельбы
        if self.player_cooldown > 0:
            self.player_cooldown -= dt

        # Движение пуль игрока
        for b in self.bullets:
            b.y -= int(self.BULLET_SPEED * dt)
        self.bullets = [b for b in self.bullets if b.bottom > 0]

        # Движение врагов
        bounds = self._enemies_rect_bounds()
        if bounds:
            need_turn = (bounds.right + int(self.enemy_speed * self.enemy_dir * dt) > w-8) or \
                        (bounds.left + int(self.enemy_speed * self.enemy_dir * dt) < 8)
            if need_turn:
                self.enemy_dir *= -1
                # опускаем всех на шаг вниз и ускоряемся чуть-чуть
                for e in self._all_enemies():
                    e.y += self.ENEMY_Y_STEP
                self.enemy_speed *= 1.06
                bounds = self._enemies_rect_bounds()

            # горизонтальное смещение
            dx = int(self.enemy_speed * self.enemy_dir * dt)
            if dx:
                for e in self._all_enemies():
                    e.x += dx

            # поражение: враги добрались до низа
            if bounds and bounds.bottom >= self.player.top - 10:
                self._lose()
                return

        # Стрельба врагов (случайно, но из нижней живой в колонке)
        self.enemy_fire_timer -= dt
        if self.enemy_fire_timer <= 0 and bounds:
            self.enemy_fire_timer = self._rand_enemy_fire_time()
            # выберем случайную колонку, найдём в ней нижнего живого
            cols = {}
            for r in range(self.ENEMY_ROWS):
                for c in range(self.ENEMY_COLS):
                    e = self.enemies[r][c]
                    if e:
                        cols.setdefault(c, []).append((r, e))
            if cols:
                c = RND.choice(list(cols.keys()))
                # нижний = с максимальным y
                r, e = max(cols[c], key=lambda it: it[1].bottom)
                bullet = pg.Rect(e.centerx - 2, e.bottom + 2, 4, 10)
                self.enemy_bullets.append(bullet)

        # Движение пуль врага
        for eb in self.enemy_bullets:
            eb.y += int(self.ENEMY_BULLET_SPEED * dt)
        self.enemy_bullets = [eb for eb in self.enemy_bullets if eb.top < h]

        # Коллизии «пуля игрока → враг»
        for b in self.bullets[:]:
            hit = False
            # ускоренная проверка: по рядам
            for r in range(self.ENEMY_ROWS):
                row = self.enemies[r]
                for c in range(self.ENEMY_COLS):
                    e = row[c]
                    if e and b.colliderect(e):
                        row[c] = None
                        hit = True
                        self.score += 10
                        break
                if hit:
                    break
            if hit:
                self.bullets.remove(b)

        # Коллизии «пуля врага → игрок»
        for eb in self.enemy_bullets[:]:
            if eb.colliderect(self.player):
                self.enemy_bullets.remove(eb)
                self.lives -= 1
                if self.lives <= 0:
                    self._lose()
                    return

        # Победа?
        any_left = any(e for e in self._all_enemies())
        if not any_left:
            self._win()
            return

    # ------------- outcomes -------------
    def _win(self):
        # ачивка и переход
        try:
            from core.ui import TOASTS
            TOASTS.push("Ачивка: Пряники", icon_name="trophy.png", ttl=2.6)
        except Exception:
            pass
        self.state.award("pryaniki")
        self.state.save()

        from scenes.cutscene import CutsceneScene
        # создаёшь data/script_ch2_oracle_end.json; далее по плану — например, «День рождения»
        self.mgr.switch(CutsceneScene, state=self.state,
                        script_file="script_ch2_birthday.json", next_scene="maze")

    def _lose(self):
        from scenes.cutscene import CutsceneScene
        # простая ретрай-заставка → вернуться в «Оракул»
        self.mgr.switch(CutsceneScene, state=self.state,
                        script_file="script_ch2_oracle_retry.json", next_scene="oracle")

    # ------------- draw -------------
    def draw(self):
        self.screen.fill((8, 10, 18))
        w, h = self.screen.get_size()

        # враги
        for e in self._all_enemies():
            pg.draw.rect(self.screen, (160, 200, 255), e, border_radius=3)

        # пули
        for b in self.bullets:
            pg.draw.rect(self.screen, (255, 245, 140), b, border_radius=2)
        for eb in self.enemy_bullets:
            pg.draw.rect(self.screen, (255, 120, 110), eb, border_radius=2)

        # игрок
        pg.draw.rect(self.screen, (110, 255, 160), self.player, border_radius=3)

        # HUD
        f = pg.font.SysFont(None, 22)
        self.screen.blit(f.render(f"Счёт: {self.score}", True, (220,220,230)), (14, 10))
        lives_txt = "Жизни: " + "❤ " * max(0, self.lives)
        self.screen.blit(f.render(lives_txt, True, (255,140,160)), (14, 34))
        self.screen.blit(f.render("← → — движение, SPACE — выстрел", True, (200,200,210)), (14, h-28))

        # Заставка (если активна)
        if self.intro and not self.intro.done:
            self.intro.draw(self.screen)
