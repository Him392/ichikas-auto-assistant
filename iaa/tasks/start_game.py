from kotonebot import device, image, task, Loop, action, sleep
from kotonebot import logging
from kotonebot.util import Throttler, Countdown

from iaa.consts import PACKAGE_NAME_JP
from . import R

logger = logging.getLogger(__name__)

@action('登录', screenshot_mode='manual')
def login():
    for _ in Loop(interval=3):
        if image.find(R.Login.TextLinkFinished):
            logger.debug('Link finished')
            logger.info('Login finishied')
            break
        if image.find(R.Login.ButtonLink):
            device.click()
            logger.debug('Clicked 連携')
        elif image.find(R.Login.ButtonIconLink):
            device.click()
            logger.debug('Clicked データ引き継ぎ')
        elif image.find(R.Login.ButtonLinkByGooglePlay):
            device.click()
            logger.debug('Clicked GooglePlayで連携')
        elif image.find(R.Login.ButtonMenu):
            device.click()
            logger.debug('Clicked 右上角菜单按钮')

@action('返回首页', screenshot_mode='manual')
def go_home():
    logger.info('Try to go home.')
    th = Throttler(1)
    cd = Countdown(4)
    for _ in Loop():
        if image.find(R.Hud.IconCrystal):
            cd.start()
            logger.debug('Crystal icon found.')
            if cd.expired():
                logger.info('Now at home.')
                break
        else:
            cd.reset()
        if th.request():
            device.click(1, 1)

@task('启动游戏', screenshot_mode='manual')
def start_game():
    d = device.of_android()
    if d.current_package() != PACKAGE_NAME_JP:
        logger.info('Not at game. Launching...')
        d.launch_app(PACKAGE_NAME_JP)
        login()
    else:
        logger.info('Already at game.')
    go_home()