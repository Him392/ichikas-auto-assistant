from kotonebot import device, image, task, Loop, action, sleep
from kotonebot import logging
from kotonebot.util import Throttler, Countdown

from iaa.config.schemas import LinkAccountOptions
from iaa.consts import PACKAGE_NAME_JP
from iaa.context import conf
from . import R

logger = logging.getLogger(__name__)

@action('登录', screenshot_mode='manual')
def login(link_account: LinkAccountOptions):
    """执行登录流程。
    
    :param link_account: 账号引继方式，目前支持 'google_play'
    """
    for _ in Loop(interval=3):
        if image.find(R.Login.TextLinkFinished):
            logger.debug('Link finished')
            logger.info('Login finished')
            break
        if image.find(R.Login.ButtonLink):
            device.click()
            logger.debug('Clicked 連携')
        elif image.find(R.Login.ButtonIconLink):
            device.click()
            logger.debug('Clicked データ引き継ぎ')
        elif link_account == 'google_play' and image.find(R.Login.ButtonLinkByGooglePlay):
            device.click()
            logger.debug('Clicked GooglePlayで連携')
        elif image.find(R.Login.ButtonMenu):
            device.click()
            logger.debug('Clicked 右上角菜单按钮')

@action('返回首页', screenshot_mode='manual')
def go_home(threshold_timeout: float = 0):
    logger.info('Try to go home.')
    th = Throttler(1)
    cd = Countdown(threshold_timeout)
    for _ in Loop():
        if image.find(R.Hud.IconCrystal):
            cd.start()
            logger.debug('Crystal icon found.')
            # 因为进入游戏后，公告弹窗会延迟弹出，因此不可以立即返回
            # 必须等待一段时间，关掉公告后再返回
            if cd.expired():
                logger.info('Now at home.')
                break
        else:
            cd.reset()
        # 有新需要数据下载
        if image.find(R.Login.TextRecommendDownloadViaWifi):
            device.click(image.expect(R.Login.ButtonDownload))
        
        if th.request():
            device.click(1, 1)

@task('启动游戏', screenshot_mode='manual')
def start_game():
    d = device.of_android()
    if d.current_package() != PACKAGE_NAME_JP:
        logger.info('Not at game. Launching...')
        d.launch_app(PACKAGE_NAME_JP)
        
        # 检查是否需要登录
        link_account = conf().game.link_account
        if link_account is not None:
            login(link_account)
        
        go_home(4)
    else:
        logger.info('Already at game.')
        go_home()
    