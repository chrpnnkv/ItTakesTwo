import os, random
import pygame as pg
from core.base_scene import BaseScene
from scenes.cutscene import CutsceneScene

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

        maze_files = [f for f in os.listdir("data/maze") if f.startswith("maze") and f.endswith(".txt")]
        chosen = random.choice(maze_files)

        self.grid = load_level(os.path.join("data/maze", chosen))
        self.player = self.find('S')
        self.exit = self.find('E')
        self.speed = 150.0

    def find(self, ch):
        for y,row in enumerate(self.grid):
            x = row.find(ch)
            if x != -1:
                return pg.Vector2(x*TILE+TILE//2, y*TILE+TILE//2)

    def tile_at(self, x, y):
        gx, gy = int(x // TILE), int(y // TILE)
        if 0 <= gy < len(self.grid) and 0 <= gx < len(self.grid[gy]):
            return self.grid[gy][gx]
        return '#'

    def passable(self, x, y):
        return self.tile_at(x, y) != '#'

    def update(self, dt):
        keys = pg.key.get_pressed()
        vx = (keys[pg.K_d] - keys[pg.K_a])
        vy = (keys[pg.K_s] - keys[pg.K_w])

        tile_here = self.tile_at(self.player.x, self.player.y)
        slow = 0.65 if tile_here == '~' else 1.0
        speed = self.speed * slow

        move = pg.Vector2(vx, vy)
        if move.length_squared() > 0:
            move = move.normalize() * speed * dt

        nx, ny = self.player.x + move.x, self.player.y
        if self.passable(nx, self.player.y):
            self.player.x = nx
        nx, ny = self.player.x, self.player.y + move.y
        if self.passable(self.player.x, ny):
            self.player.y = ny

        if (self.player - self.exit).length() < 14:
            self.state.award("stertye_nogi")
            self.state.save()
            self.mgr.switch(CutsceneScene, state=self.state,
                            script_file="script_ch3.json", next_scene="end")

    def draw(self):
        self.screen.fill((10, 10, 14))
        for y, row in enumerate(self.grid):
            for x, ch in enumerate(row):
                r = pg.Rect(x * TILE, y * TILE, TILE, TILE)
                if ch == '#':
                    pg.draw.rect(self.screen, (40, 40, 60), r)
                elif ch == '~':
                    pg.draw.rect(self.screen, (30, 70, 70), r)
        pg.draw.circle(self.screen, (230, 230, 255), self.player, 10)
        pg.draw.circle(self.screen, (120, 200, 160), self.exit, 10)