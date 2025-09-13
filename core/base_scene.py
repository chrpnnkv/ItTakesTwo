class BaseScene:
    def __init__(self, manager):
        self.mgr = manager
        self.screen = manager.screen

    def handle_event(self, event): pass
    def update(self, dt): pass
    def draw(self): pass
