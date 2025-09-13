class SceneManager:
    def __init__(self, screen, start_scene):
        self.screen = screen
        self.scene = start_scene(self)

    def switch(self, scene_cls, **kwargs):
        self.scene = scene_cls(self, **kwargs)

    def handle_event(self, event):
        self.scene.handle_event(event)

    def update(self, dt):
        self.scene.update(dt)

    def draw(self):
        self.scene.draw()
