import pygame as pg
from core.scene_manager import SceneManager
from scenes.menu import MenuScene

WIDTH, HEIGHT = 960, 540
FPS = 60

def main():
    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()
    manager = SceneManager(screen, start_scene=MenuScene)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            manager.handle_event(event)
        manager.update(dt)
        manager.draw()
        pg.display.flip()

    pg.quit()

if __name__ == "__main__":
    main()
