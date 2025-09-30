import os, random
import pygame as pg
from core.base_scene import BaseScene
from scenes.cutscene import CutsceneScene
from core.anim import AnimatedSprite  # <-- добавили
from core.ui import TOASTS            # для тоста при победе

TILE = 32

def load_level(path):
    with open(path, "r", encoding="utf-8") as f:
        rows = [line.rstrip("\n") for line in f if line.strip()]
    width = max(len(r) for r in rows)
    rows = [r.ljust(width, "#") for r in rows]
    return rows

class MazeGame(BaseScene):
    def __init__(self, manager, state):
        super().__init__(manager)
        self.state = state

        # выбираем одну из карт случайно
        maze_files = [f for f in os.listdir("data/maze") if f.startswith("maze") and f.endswith(".txt")]
        chosen = random.choice(maze_files)

        self.grid = load_level(os.path.join("data/maze", chosen))
        spawn = self.find('S')
        self.exit = self.find('E')
        self.speed = 150.0

        # игрок как анимированный спрайт
        self.player = AnimatedSprite(base_dir="character", fps=10, scale=1.0)
        # если в карте нет 'S', поставим в центр экрана как fallback
        if spawn is None:
            w, h = self.screen.get_size()
            spawn = pg.Vector2(w//2, h//2)
        self.player.pos.update(spawn.x, spawn.y)

    def find(self, ch):
        for y, row in enumerate(self.grid):
            x = row.find(ch)
            if x != -1:
                return pg.Vector2(x*TILE + TILE//2, y*TILE + TILE//2)

    def tile_at(self, x, y):
        gx, gy = int(x // TILE), int(y // TILE)
        if 0 <= gy < len(self.grid) and 0 <= gx < len(self.grid[gy]):
            return self.grid[gy][gx]
        return '#'

    def passable(self, x, y):
        return self.tile_at(x, y) != '#'

    def update(self, dt):
        keys = pg.key.get_pressed()
        vx = (keys[pg.K_d] or keys[pg.K_RIGHT]) - (keys[pg.K_a] or keys[pg.K_LEFT])
        vy = (keys[pg.K_s] or keys[pg.K_DOWN]) - (keys[pg.K_w] or keys[pg.K_UP])

        # направление анимации
        moving = (vx != 0 or vy != 0)
        dir_name = self.player.direction
        if abs(vx) > abs(vy):
            dir_name = "left" if vx < 0 else "right"
        elif vy != 0:
            dir_name = "forward" if vy > 0 else "back"
        self.player.set_direction(dir_name)

        # скорость с учётом замедляющих тайлов
        tile_here = self.tile_at(self.player.pos.x, self.player.pos.y)
        slow = 0.65 if tile_here == '~' else 1.0
        speed = self.speed * slow

        # движение с поочерёдной проверкой коллизий по осям
        move = pg.Vector2(float(vx), float(vy))
        if move.length_squared() > 0:
            move = move.normalize() * speed * dt

            # X
            old_x = self.player.pos.x
            nx = self.player.pos.x + move.x
            if self.passable(nx, self.player.pos.y):
                self.player.pos.x = nx
            else:
                self.player.pos.x = old_x
            # Y
            old_y = self.player.pos.y
            ny = self.player.pos.y + move.y
            if self.passable(self.player.pos.x, ny):
                self.player.pos.y = ny
            else:
                self.player.pos.y = old_y

        # обновляем анимацию шага
        self.player.update(dt, moving)

        # достижение выхода
        if self.exit and (self.player.pos - self.exit).length() < 14:
            self.state.award("stertye_nogi")
            TOASTS.push("Ачивка: Стертые ноги", icon_name="trophy.png", ttl=2.8)
            self.state.save()
            self.mgr.switch(CutsceneScene, state=self.state,
                            script_file="ch2/script_ch2_messages.json", next_scene="oracle")

    def draw(self):
        self.screen.fill((10, 10, 14))
        for y, row in enumerate(self.grid):
            for x, ch in enumerate(row):
                r = pg.Rect(x * TILE, y * TILE, TILE, TILE)
                if ch == '#':
                    pg.draw.rect(self.screen, (40, 40, 60), r)
                elif ch == '~':
                    pg.draw.rect(self.screen, (30, 70, 70), r)

        # выход и игрок-спрайт
        if self.exit:
            pg.draw.circle(self.screen, (120, 200, 160), (int(self.exit.x), int(self.exit.y)), 10)
        self.player.draw(self.screen)

        tip = pg.font.SysFont(None, 22).render("WASD — движение; проводи Варюшу до дома", True,
                                               (210, 210, 210))
        self.screen.blit(tip, (30, 500))
