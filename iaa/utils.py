import os
from importlib import resources

from kotonebot import logging

logger = logging.getLogger(__name__)

def sprite_path(path: str) -> str:
    standalone = os.path.join('iaa/res/sprites', path)
    if os.path.exists(standalone):
        return standalone
    return str(resources.files('iaa.res.sprites') / path)