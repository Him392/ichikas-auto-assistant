from kotonebot import device, image, task, Loop, action, sleep, color

from kotonebot.backend.core import HintBox

from . import R

@action('是否位于首页')
def at_home() -> bool:
    return image.find(R.Hud.IconCrystal) is not None

def has_red_dot(box: HintBox) -> bool:
    return color.find('#ff5589', rect=box) is not None