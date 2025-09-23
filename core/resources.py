import pygame as pg
import json
import os

_ASSET_CACHE = {"img":{}, "font":{}, "sfx":{}, "music":{}}

def img(path):
    if path not in _ASSET_CACHE["img"]:
        _ASSET_CACHE["img"][path] = pg.image.load(os.path.join("assets","img",path)).convert_alpha()
    return _ASSET_CACHE["img"][path]

def font(name, size):
    key = (name,size)
    if key not in _ASSET_CACHE["font"]:
        _ASSET_CACHE["font"][key] = pg.font.Font(os.path.join("assets","fonts",name), size)
    return _ASSET_CACHE["font"][key]

def load_json(path):
    with open(os.path.join("data", path), "r", encoding="utf-8") as f:
        return json.load(f)

def sfx(path):
    """Загрузить короткий звук (WAV/OGG) из assets/sfx/"""
    if path not in _ASSET_CACHE["sfx"]:
        _ASSET_CACHE["sfx"][path] = pg.mixer.Sound(os.path.join("assets", "sfx", path))
    return _ASSET_CACHE["sfx"][path]