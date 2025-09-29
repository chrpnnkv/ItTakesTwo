# scenes/birthday_game.py
import pygame as pg
from core.base_scene import BaseScene


class BirthdayGame(BaseScene):
    """
    Мини-игра «День рождения» — арканоид.
    """
    def __init__(self, manager, state):
        super().__init__(manager)
        self.state = state
        w, h = self.screen.get_size()

        # платформа
        self.paddle = pg.Rect(w//2 - 50, h - 40, 100, 16)
        self.paddle_speed = 360

        # мяч
        self.ball = pg.Rect(w//2 - 8, h//2, 16, 16)
        self.ball_vel = pg.Vector2(200, -240)

        # блоки
        self.blocks = []
        rows, cols = 5, 10
        margin_x, margin_y = 60, 60
        bw, bh = 64, 24
        for r in range(rows):
            for c in range(cols):
                x = margin_x + c*bw
                y = margin_y + r*bh
                self.blocks.append(pg.Rect(x, y, bw-4, bh-4))

        self.lives = 3

    # ---------------- EVENTS ----------------
    def handle_event(self, e):
        pass

    # ---------------- UPDATE ----------------
    def update(self, dt):
        keys = pg.key.get_pressed()
        vx = (keys[pg.K_d] or keys[pg.K_RIGHT]) - (keys[pg.K_a] or keys[pg.K_LEFT])
        self.paddle.x += int(vx * self.paddle_speed * dt)
        self.paddle.clamp_ip(self.screen.get_rect())

        # движение мяча
        self.ball.x += int(self.ball_vel.x * dt)
        self.ball.y += int(self.ball_vel.y * dt)

        # отражения от стен
        if self.ball.left <= 0 or self.ball.right >= self.screen.get_width():
            self.ball_vel.x *= -1
        if self.ball.top <= 0:
            self.ball_vel.y *= -1

        # падение мяча
        if self.ball.top >= self.screen.get_height():
            self.lives -= 1
            if self.lives <= 0:
                self._lose()
                return
            # рестарт мяча
            self.ball.center = (self.screen.get_width()//2, self.screen.get_height()//2)
            self.ball_vel = pg.Vector2(200, -240)

        # отражение от платформы
        if self.ball.colliderect(self.paddle) and self.ball_vel.y > 0:
            offset = (self.ball.centerx - self.paddle.centerx) / (self.paddle.width/2)
            self.ball_vel = pg.Vector2(offset*240, -abs(self.ball_vel.y))

        # блоки
        hit = None
        for b in self.blocks:
            if self.ball.colliderect(b):
                hit = b
                break
        if hit:
            self.blocks.remove(hit)
            self.ball_vel.y *= -1

        # победа
        if not self.blocks:
            self._win()

    # ---------------- OUTCOMES ----------------
    def _win(self):
        try:
            from core.ui import TOASTS
            TOASTS.push("Ачивка: Командирские часы", icon_name="trophy.png", ttl=2.6)
        except Exception:
            pass
        self.state.award("birthday")
        self.state.save()

        from scenes.cutscene import CutsceneScene
        self.mgr.switch(CutsceneScene, state=self.state,
                        script_file="script_ch2_birthday_end.json", next_scene="end")

    def _lose(self):
        from scenes.cutscene import CutsceneScene
        self.mgr.switch(CutsceneScene, state=self.state,
                        script_file="script_ch2_birthday_retry.json", next_scene="birthday")

    # ---------------- DRAW ----------------
    def draw(self):
        self.screen.fill((15, 10, 20))

        # блоки
        for b in self.blocks:
            pg.draw.rect(self.screen, (200, 160, 100), b)

        # платформа
        pg.draw.rect(self.screen, (120,220,120), self.paddle)

        # мяч
        pg.draw.ellipse(self.screen, (255,240,150), self.ball)

        # HUD
        f = pg.font.SysFont(None, 22)
        self.screen.blit(f.render(f"Жизни: {self.lives}", True, (230,230,230)), (16, 10))
