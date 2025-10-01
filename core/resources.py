import pygame as pg
import json
import os

_ASSET_CACHE = {"img":{}, "font":{}, "sfx":{}, "music":{}}
def img(name):
    # If name contains a path delimiter, use it directly
    for subdir in ['', 'ch1/', 'ch2/', 'ch3/', 'ch4/']:
        path = os.path.join('assets', 'img', subdir + name)
        if os.path.exists(path):
            return pg.image.load(path).convert_alpha()
    raise FileNotFoundError(f"Image not found: {name}")

def load_json(filename):
    for subdir in ['', 'ch1/', 'ch2/', 'ch3/', 'ch4/']:
        path = os.path.join('data', subdir + filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    raise FileNotFoundError(f"JSON not found: {filename}")

def font(name, size):
    key = (name,size)
    if key not in _ASSET_CACHE["font"]:
        _ASSET_CACHE["font"][key] = pg.font.Font(os.path.join("assets","fonts",name), size)
    return _ASSET_CACHE["font"][key]

def sfx(path):
    """Загрузить короткий звук (WAV/OGG) из assets/sfx/"""
    if path not in _ASSET_CACHE["sfx"]:
        _ASSET_CACHE["sfx"][path] = pg.mixer.Sound(os.path.join("assets", "sfx", path))
    return _ASSET_CACHE["sfx"][path]