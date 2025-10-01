import random
import pygame as pg
from core.anim import AnimatedSprite
from core.resources import img
from core.base_scene import BaseScene
from core.ui import MiniIntro

RND = random.Random()

class ConcertGame(BaseScene):
    def __init__(self, manager, state):
        super().__init__(manager)
        self.state = state

        # фон (танцпол)
        self.bg = img("ch1_dancefloor.png")  # assets/img/ch1_dancefloor.png

        w, h = self.screen.get_size()

        # игрок
        self.hp = 100
        self.player_speed = 200
        self.player = AnimatedSprite(base_dir="character", fps=10, scale=1.0)
        self.player.pos.update(100, 140)  # стартовая позиция

        # враги «верзилы»
        self.n_bullies = 8
        self.bully_min_speed = 50
        self.bully_max_speed = 210
        self.bully_change_dir_min = 0.8
        self.bully_change_dir_max = 5.0
        self.bully_aggro_radius = 400
        self.bully_radius = 14
        self.damage_per_sec = 60

        # «напитки»
        self.max_drinks = 8
        self.drink_radius = 8
        self.heal_on_pickup = 25

        # выход
        self.exit_rect = pg.Rect(820, 440, 100, 80)

        # спавним врагов и напитки
        self.bullies = []
        for _ in range(self.n_bullies):
            pos = pg.Vector2(RND.randint(100, w - 100), RND.randint(100, h - 60))
            vel = self._random_dir() * RND.uniform(self.bully_min_speed, self.bully_max_speed)
            timer = RND.uniform(self.bully_change_dir_min, self.bully_change_dir_max)
            self.bullies.append({"pos": pos, "vel": vel, "timer": timer})

        self.drinks = [pg.Vector2(RND.randint(80, w - 80), RND.randint(80, h - 40))
                       for _ in range(self.max_drinks)]

        # кулдаун для запрета «саморегенерации»
        self.regen_cooldown = 0.0

        self.intro = MiniIntro(
            [
                ("МИНИ-ИГРА", 40, (235, 235, 240)),
                ("Концерт", 32, (255, 230, 150)),
                ("Цель: доберись до выхода, избегая толпы", 22, (220, 220, 230)),
            ],
            bg_color=(245, 185, 25),  # жёлтый фон как на скрине (опционально)
            auto_start_after=None,  # можно поставить, например, 2.0
            fade_in=0.6,  # было 0.35
            start_delay_step=0.30,  # было 0.18
            bg_image="ch1/ch1_dancefloor.png"
        )

    # ---------------- utils ----------------
    def _random_dir(self) -> pg.Vector2:
        v = pg.Vector2(RND.uniform(-1, 1), RND.uniform(-1, 1))
        if v.length_squared() == 0:
            v = pg.Vector2(1, 0)
        return v.normalize()

    def _clamp_in_screen(self, pos: pg.Vector2):
        w, h = self.screen.get_size()
        pos.x = max(20, min(w - 20, pos.x))
        pos.y = max(20, min(h - 20, pos.y))

    # ---------------- events ----------------
    def handle_event(self, e):
        if self.intro and not self.intro.done:
            self.intro.handle_event(e)
            return

    # ---------------- loop ----------------
    def update(self, dt):
        if self.intro and not self.intro.done:
            self.intro.update(dt)
            return

        keys = pg.key.get_pressed()

        # движение игрока
        vx = (keys[pg.K_d] or keys[pg.K_RIGHT]) - (keys[pg.K_a] or keys[pg.K_LEFT])
        vy = (keys[pg.K_s] or keys[pg.K_DOWN]) - (keys[pg.K_w] or keys[pg.K_UP])
        move = pg.Vector2(float(vx), float(vy))

        moving = move.length_squared() > 0
        if moving:
            move = move.normalize() * self.player_speed * dt
            # направление анимации
            if abs(move.x) > abs(move.y):
                self.player.set_direction("left" if move.x < 0 else "right")
            else:
                self.player.set_direction("back" if move.y < 0 else "forward")
            # применяем перемещение
            self.player.pos += move
            self._clamp_in_screen(self.player.pos)
        else:
            # стоим — первый кадр анимации
            self.player.update(0, False)

        # анимация шага
        self.player.update(dt, moving)

        # поведение «верзил»
        w, h = self.screen.get_size()
        for b in self.bullies:
            b["timer"] -= dt
            if b["timer"] <= 0:
                new_dir = self._random_dir()
                new_spd = RND.uniform(self.bully_min_speed, self.bully_max_speed)
                b["vel"] = new_dir * new_spd
                b["timer"] = RND.uniform(self.bully_change_dir_min, self.bully_change_dir_max)

            to_player = self.player.pos - b["pos"]
            dist2 = to_player.length_squared()
            if 0 < dist2 < self.bully_aggro_radius ** 2:
                # немного «подруливать» к игроку
                steer = to_player.normalize() * 1500
                b["vel"] = (b["vel"] + steer * dt).normalize() * max(60, b["vel"].length())

            b["pos"] += b["vel"] * dt
            bounced = False
            if b["pos"].x < 20 or b["pos"].x > w - 20:
                b["vel"].x *= -1; bounced = True
            if b["pos"].y < 20 or b["pos"].y > h - 20:
                b["vel"].y *= -1; bounced = True
            if bounced:
                self._clamp_in_screen(b["pos"])

        # урон от «верзил»
        was_hit = any((b["pos"] - self.player.pos).length() < (self.bully_radius + 12) for b in self.bullies)
        if was_hit:
            self.hp -= self.damage_per_sec * dt
            self.regen_cooldown = 0.0  # на будущее, если введёшь реген

        # подбор «напитков»
        picked = [d for d in self.drinks if (d - self.player.pos).length() < (self.drink_radius + 12)]
        if picked:
            self.hp = min(100, self.hp + self.heal_on_pickup * len(picked))
            self.drinks = [d for d in self.drinks if (d - self.player.pos).length() >= (self.drink_radius + 12)]

        # смерть → retry-катсцена
        self.hp = max(0, min(100, self.hp))
        if self.hp <= 0:
            from scenes.cutscene import CutsceneScene
            self.mgr.switch(CutsceneScene, state=self.state,
                            script_file="ch1/script_ch1_retry.json", next_scene="concert")
            return

        # победа — дошли до выхода
        if self.exit_rect.collidepoint(int(self.player.pos.x), int(self.player.pos.y)):
            self.state.award("da_ya_zhestkii")
            from core.ui import TOASTS
            TOASTS.push("Ачивка: Да я жёсткий", icon_name="trophy.png", ttl=2.8)
            self.state.save()
            from scenes.cutscene import CutsceneScene
            self.mgr.switch(CutsceneScene, state=self.state,
                            script_file="ch1/script_ch1_durak.json", next_scene="balance")
            return

    def draw(self):
        if self.intro and not self.intro.done:
            self.intro.draw(self.screen)
            return  # (если хочешь полностью перекрывать фон игры на время интро)

        # фон
        self.screen.blit(self.bg, (0, 0))

        # выход
        pg.draw.rect(self.screen, (60, 180, 120), self.exit_rect)

        # враги
        for b in self.bullies:
            pg.draw.circle(self.screen, (180, 60, 60), (int(b["pos"].x), int(b["pos"].y)), self.bully_radius)

        # напитки
        for d in self.drinks:
            pg.draw.circle(self.screen, (200, 200, 80), (int(d.x), int(d.y)), self.drink_radius)

        # игрок-спрайт
        self.player.draw(self.screen)

        # HP бар
        pg.draw.rect(self.screen, (60, 60, 60), (30, 20, 300, 16))
        w = int(300 * max(0, min(1, self.hp / 100)))
        pg.draw.rect(self.screen, (120, 220, 120), (30, 20, w, 16))

        # подсказка
        tip = pg.font.SysFont(None, 22).render(
            "WASD — двигайся, избегай верзил, подбирай напитки", True, (220, 220, 230))
        self.screen.blit(tip, (30, 500))
