# tools/make_placeholders.py
import os, math, wave, struct
import pygame as pg

BASE = os.path.dirname(os.path.dirname(__file__))
IMG_DIR = os.path.join(BASE, "assets", "img")
SFX_DIR = os.path.join(BASE, "assets", "sfx")
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(SFX_DIR, exist_ok=True)

# 1) trophy.png — рисуем простую «чашу» и сохраняем
pg.init()
surf = pg.Surface((64, 64), pg.SRCALPHA)
# ножка
pg.draw.rect(surf, (230, 200, 70), pg.Rect(28, 42, 8, 10), border_radius=2)
pg.draw.rect(surf, (190, 160, 50), pg.Rect(18, 52, 28, 6), border_radius=2)
# чаша
pg.draw.ellipse(surf, (230, 200, 70), pg.Rect(12, 10, 40, 24))
pg.draw.rect(surf, (230, 200, 70), pg.Rect(20, 22, 24, 12))
# ручки
pg.draw.arc(surf, (230, 200, 70), pg.Rect(4, 12, 20, 20), math.pi*0.1, math.pi*0.9, 4)
pg.draw.arc(surf, (230, 200, 70), pg.Rect(40, 12, 20, 20), math.pi*0.1 + math.pi, math.pi*0.9 + math.pi, 4)

trophy_path = os.path.join(IMG_DIR, "trophy.png")
pg.image.save(surf, trophy_path)
print("Saved:", trophy_path)

# 2) achieve.wav — генерируем короткий «дзынь» (синус, 880 Гц → 1320 Гц)
rate = 44100
dur  = 0.25  # сек
samples = int(rate * dur)
f1, f2 = 880.0, 1320.0

wav_path = os.path.join(SFX_DIR, "achieve.wav")
with wave.open(wav_path, "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)  # 16-bit
    wf.setframerate(rate)
    for i in range(samples):
        t = i / rate
        # линейный свип от f1 к f2
        f = f1 + (f2 - f1) * (i / samples)
        amp = 0.35 * (1 - i / samples)  # затухание
        val = int(amp * 32767 * math.sin(2 * math.pi * f * t))
        wf.writeframesraw(struct.pack("<h", val))
print("Saved:", wav_path)
