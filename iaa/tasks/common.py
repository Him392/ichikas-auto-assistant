from kotonebot import device, image, task, Loop, action, sleep, color

from . import R

@action('是否位于首页')
def at_home() -> bool:
    return image.find(R.Hud.IconCrystal) is not None