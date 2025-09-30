import json, os, tempfile, shutil

class GameState:
    def __init__(self):
        self.chapter = 1
        self.achievements = set()

    def award(self, key):
        self.achievements.add(key)

    def has_save(self, slot="slot1.json") -> bool:
        path = os.path.join("saves", slot)
        return os.path.exists(path) and os.path.getsize(path) > 0

    def save(self, slot="slot1.json"):
        os.makedirs("saves", exist_ok=True)
        data = {"chapter": self.chapter, "achievements": list(self.achievements)}
        tmp_dir = "saves"
        fd, tmp_path = tempfile.mkstemp(prefix=".__save_", dir=tmp_dir, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            final_path = os.path.join("saves", slot)
            shutil.move(tmp_path, final_path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    def load(self, slot="slot1.json"):
        path = os.path.join("saves", slot)
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            self.chapter = 1
            self.achievements = set()
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.chapter = int(data.get("chapter", 1))
            self.achievements = set(data.get("achievements", []))
            return True
        except Exception:
            self.chapter = 1
            self.achievements = set()
            return False
