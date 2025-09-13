import random, pygame as pg
from core.base_scene import BaseScene
from scenes.cutscene import CutsceneScene

class ConcertGame(BaseScene):
    def __init__(self, manager, state):
        super().__init__(manager)
        self.state = state
        self.player = pg.Vector2(60, 60)
        self.hp = 100
        self.exit_rect = pg.Rect(820, 40, 100, 80)
        self.bullies = [pg.Vector2(random.randint(100,860), random.randint(100,460)) for _ in range(12)]
        self.drinks = [pg.Vector2(random.randint(80,880), random.randint(80,500)) for _ in range(8)]

    def handle_event(self, e): pass

    def update(self, dt):
        keys = pg.key.get_pressed()
        v = pg.Vector2((keys[pg.K_d]-keys[pg.K_a])*200, (keys[pg.K_s]-keys[pg.K_w])*200)
        self.player += v*dt
        self.player.x = max(20, min(940, self.player.x))
        self.player.y = max(20, min(520, self.player.y))

        for b in self.bullies:
            if (b - self.player).length() < 28:
                self.hp -= 30*dt
        self.drinks[:] = [d for d in self.drinks if (d - self.player).length() >= 24]
        if len(self.drinks) < 8: self.hp = min(100, self.hp + 15*dt)

        if self.hp <= 0:
            self.mgr.switch(CutsceneScene, state=self.state,
                            script_file="script_ch1.json", next_scene="concert")  # повтор
        if self.exit_rect.collidepoint(self.player.x, self.player.y):
            self.state.award("da_ya_zhestkii")
            self.state.save()
            self.mgr.switch(CutsceneScene, state=self.state,
                            script_file="script_ch2.json", next_scene="maze")

    def draw(self):
        self.screen.fill((25,15,25))
        pg.draw.rect(self.screen, (60,180,120), self.exit_rect)
        pg.draw.circle(self.screen, (230,230,255), self.player, 12)
        for b in self.bullies:
            pg.draw.circle(self.screen, (180,60,60), b, 14)
        for d in self.drinks:
            pg.draw.circle(self.screen, (200,200,80), d, 8)
        pg.draw.rect(self.screen, (60,60,60), (30, 20, 300, 16))
        w = int(300 * max(0, min(1, self.hp/100)))
        pg.draw.rect(self.screen, (120,220,120), (30, 20, w, 16))
