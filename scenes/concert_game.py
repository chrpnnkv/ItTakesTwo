import random, pygame as pg
from core.base_scene import BaseScene

RND = random.Random()


class ConcertGame(BaseScene):
    def __init__(self, manager, state):
        super().__init__(manager)
        self.state = state
        self.player = pg.Vector2(60, 60)
        self.hp = 100
        self.player_speed = 200

        self.n_bullies = 12
        self.bully_min_speed = 50
        self.bully_max_speed = 210
        self.bully_change_dir_min = 0.8
        self.bully_change_dir_max = 5.0
        self.bully_aggro_radius = 400
        self.bully_radius = 14
        self.damage_per_sec = 30

        self.max_drinks = 8
        self.drink_radius = 8
        self.heal_on_pickup = 25

        self.exit_rect = pg.Rect(820, 440, 100, 80)
        w, h = self.screen.get_size()
        self.bullies = []
        for _ in range(self.n_bullies):
            pos = pg.Vector2(RND.randint(100, w - 100), RND.randint(100, h - 60))
            vel = self._random_dir() * RND.uniform(self.bully_min_speed, self.bully_max_speed)
            timer = RND.uniform(self.bully_change_dir_min, self.bully_change_dir_max)
            self.bullies.append({"pos": pos, "vel": vel, "timer": timer})
        self.drinks = [pg.Vector2(RND.randint(80, w - 80), RND.randint(80, h - 40)) for _ in range(self.max_drinks)]

        self.regen_cooldown = 0.0

    def _random_dir(self) -> pg.Vector2:
        v = pg.Vector2(RND.uniform(-1, 1), RND.uniform(-1, 1))
        if v.length_squared() == 0:
            v = pg.Vector2(1, 0)
        return v.normalize()

    def _clamp_in_screen(self, v: pg.Vector2):
        w, h = self.screen.get_size()
        v.x = max(20, min(w - 20, v.x))
        v.y = max(20, min(h - 20, v.y))

    def handle_event(self, e):
        pass

    def update(self, dt):
        keys = pg.key.get_pressed()
        move = pg.Vector2((keys[pg.K_d] - keys[pg.K_a]), (keys[pg.K_s] - keys[pg.K_w]))
        if move.length_squared() > 0:
            move = move.normalize() * self.player_speed
        self.player += move * dt
        self._clamp_in_screen(self.player)

        w, h = self.screen.get_size()
        for b in self.bullies:
            b["timer"] -= dt
            if b["timer"] <= 0:
                new_dir = self._random_dir()
                new_spd = RND.uniform(self.bully_min_speed, self.bully_max_speed)
                b["vel"] = new_dir * new_spd
                b["timer"] = RND.uniform(self.bully_change_dir_min, self.bully_change_dir_max)

            to_player = self.player - b["pos"]
            dist2 = to_player.length_squared()
            if dist2 < self.bully_aggro_radius ** 2 and dist2 > 0:
                steer = to_player.normalize() * 1500
                b["vel"] = (b["vel"] + steer * dt).normalize() * b["vel"].length()

            b["pos"] += b["vel"] * dt
            bounced = False
            if b["pos"].x < 20 or b["pos"].x > w - 20:
                b["vel"].x *= -1
                bounced = True
            if b["pos"].y < 20 or b["pos"].y > h - 20:
                b["vel"].y *= -1
                bounced = True
            if bounced:
                self._clamp_in_screen(b["pos"])

        was_hit = False
        for b in self.bullies:
            if (b["pos"] - self.player).length() < (self.bully_radius + 12):  # 12 ~ радиус игрока
                was_hit = True
                break
        if was_hit:
            self.hp -= self.damage_per_sec * dt
            self.regen_cooldown = 2.0

        picked = [d for d in self.drinks if (d - self.player).length() < 24]
        picked = [d for d in self.drinks if (d - self.player).length() < (self.drink_radius + 12)]
        if picked:
            self.hp = min(100, self.hp + self.heal_on_pickup * len(picked))
            self.drinks = [d for d in self.drinks if (d - self.player).length() >= (self.drink_radius + 12)]

        self.hp = max(0, min(100, self.hp))
        if self.hp <= 0:
            from scenes.concert_game import ConcertGame
            self.mgr.switch(ConcertGame, state=self.state)
        if self.exit_rect.collidepoint(self.player.x, self.player.y):
            self.state.award("da_ya_zhestkii")
            self.state.save()
            from scenes.cutscene import CutsceneScene
            self.mgr.switch(CutsceneScene, state=self.state,
                            script_file="script_ch2.json", next_scene="maze")

    def draw(self):
        self.screen.fill((25, 15, 25))
        pg.draw.rect(self.screen, (60, 180, 120), self.exit_rect)
        pg.draw.circle(self.screen, (230, 230, 255), self.player, 12)
        for b in self.bullies:
            pg.draw.circle(self.screen, (180, 60, 60), b["pos"], self.bully_radius)
        for d in self.drinks:
            pg.draw.circle(self.screen, (200, 200, 80), d, self.drink_radius)
        pg.draw.rect(self.screen, (60, 60, 60), (30, 20, 300, 16))
        w = int(300 * max(0, min(1, self.hp / 100)))
        pg.draw.rect(self.screen, (120, 220, 120), (30, 20, w, 16))
        tip = pg.font.SysFont(None, 22).render("WASD — движение, избегай верзил, подбирай напитки", True,
                                               (210, 210, 210))
        self.screen.blit(tip, (30, 44))
