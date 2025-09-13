import pygame as pg
from core.base_scene import BaseScene
from scenes.cutscene import CutsceneScene

TILE = 32
LEVEL = [
    "############################",
    "#S.....#..........#.......E#",
    "#.###..#..####....#..###...#",
    "#.............#####......#.#",
    "########......#..........#.#",
    "#.........................##",
    "############################",
]

class MazeGame(BaseScene):
    def __init__(self, manager, state):
        super().__init__(manager)
        self.state = state
        self.grid = LEVEL
        self.player = self.find('S')
        self.exit = self.find('E')

    def find(self, ch):
        for y,row in enumerate(self.grid):
            x = row.find(ch)
            if x != -1:
                return pg.Vector2(x*TILE+TILE//2, y*TILE+TILE//2)

    def passable(self, x, y):
        gx, gy = int(x//TILE), int(y//TILE)
        return self.grid[gy][gx] != '#'

    def update(self, dt):
        keys = pg.key.get_pressed()
        dx = (keys[pg.K_d]-keys[pg.K_a]) * 150 * dt
        dy = (keys[pg.K_s]-keys[pg.K_w]) * 150 * dt
        nx, ny = self.player.x + dx, self.player.y + dy
        if self.passable(nx, self.player.y): self.player.x = nx
        if self.passable(self.player.x, ny): self.player.y = ny

        if (self.player - self.exit).length() < 16:
            self.state.award("stertye_nogi")
            self.state.save()
            self.mgr.switch(CutsceneScene, state=self.state,
                            script_file="script_ch3.json", next_scene="end")

    def draw(self):
        self.screen.fill((10,10,14))
        for y,row in enumerate(self.grid):
            for x,ch in enumerate(row):
                r = pg.Rect(x*TILE, y*TILE, TILE, TILE)
                if ch == '#':
                    pg.draw.rect(self.screen, (40,40,60), r)
        pg.draw.circle(self.screen, (230,230,255), self.player, 10)
        pg.draw.circle(self.screen, (120,200,160), self.exit, 10)
