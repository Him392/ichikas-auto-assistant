from typing import Literal
from kotonebot import logging
from kotonebot import device, image, task, Loop, action, sleep, color

from . import R
from .start_game import go_home
from .common import at_home
from iaa.consts import PACKAGE_NAME_JP

logger = logging.getLogger(__name__)

@action('开始演出', screenshot_mode='manual')
def start_live(
        auto_setting: Literal['all'] | Literal['once'] | int | None = 'all'
    ):
    """
    前置：位于编队界面\n
    结束：首页

    :param auto_setting: 自动演出设置。\n
        * `"all"`: 自动演出直到 AP 不足
        * 任意整数: 自动演出指定次数
        * `"once"`: 自动演出一次
        * `None`: 不自动演出
    """
    if auto_setting is None or isinstance(auto_setting, int):
        raise NotImplementedError('Not implemented yet.')
    # 设置自动演出设置
    if auto_setting == 'all':
        chose = False
        for _ in Loop(interval=0.6):
            if image.find(R.Live.ButtonAutoLiveSettings):
                device.click()
                logger.debug('Clicked auto live settings button.')
            elif not chose and image.find(R.Live.TextAutoLiveUntilInsufficient):
                device.click()
                logger.debug('Chose auto live until insufficient AP.')
                sleep(0.3)
                chose = True
            elif image.find(R.Live.ButtonDecideAutoLive):
                device.click()
                logger.debug('Clicked decide auto live button.')
                sleep(0.3)
                break
    elif auto_setting == 'once':
        for _ in Loop(interval=0.6):
            if image.find(R.Live.SwitchAutoLiveOn):
                logger.debug('Auto live switch checked on.')
                break
            elif image.find(R.Live.SwitchAutoLiveOff):
                device.click()
                logger.debug('Clicked auto live switch.')
                sleep(0.3)
    logger.info('Auto live setting finished.')
    
    # 开始并等待完成
    logger.debug('Clicking start live button.')
    device.click(image.expect_wait(R.Live.ButtonStartLive))
    sleep(74.8 + 5) # 孑然妒火（最短曲） + 5s 缓冲
    # 多次自动
    if auto_setting == 'all' or isinstance(auto_setting, int):
        all_completed = False
        for _ in Loop():
            if image.find(R.Live.TextAutoLiveCompleted):
                device.click(1, 1)
                logger.info('Auto lives all completed.')
                sleep(1)
                all_completed = True
            elif all_completed and image.find(R.Live.ButtonLiveCompletedOk):
                device.click()
                logger.debug('Clicked ok button.')
                sleep(1)
                break
    # 单次自动
    elif auto_setting == 'once':
        logger.debug('Waiting for LIVE CLEAR')
        image.expect_wait(R.Live.TextLiveClear, threshold=0.7, timeout=-1)
        while not at_home():
            logger.debug('Not at home. Clicking...')
            device.click(1, 1)
            sleep(0.3)


@action('选歌', screenshot_mode='manual')
def song_select():
    """
    前置：位于选歌界面\n
    结束：位于编队界面
    """
    for _ in Loop(interval=0.6):
        if image.find(R.Live.ButtonDecide):
            device.click()
            logger.debug('Clicked start live button.')
            break
    logger.info('Song select finished.')

@action('单人演出', screenshot_mode='manual')
def solo_live():
    # 进入单人演出
    for _ in Loop(interval=0.6):
        if image.find(R.Hud.ButtonLive, threshold=0.55):
            device.click()
            logger.debug('Clicked home LIVE button.')
        elif image.find(R.Live.ButtonSoloLive):
            device.click()
            logger.debug('Clicked SoloLive button.')
        elif image.find(R.Live.ButtonDecide):
            logger.debug('Now at song select.')
            break
    
    song_select()
    start_live('all')

@action('挑战演出', screenshot_mode='manual')
def challenge_live(
    character
):
    # 进入挑战演出
    for _ in Loop(interval=0.6):
        if image.find(R.Hud.ButtonLive, threshold=0.55):
            device.click()
            logger.debug('Clicked home LIVE button.')
        elif image.find(R.Live.ButtonChallengeLive):
            if not color.find('#ff5589', rect=R.Live.BoxChallengeLiveRedDot):
                logger.info("Today's challenge live already cleared.")
                return
            device.click()
            logger.debug('Clicked ChallengeLive button.')
        elif image.find(R.Live.ChallengeLive.TextSelectCharacter):
            logger.debug('Now at character select.')
            break
    # 选择角色
    # HACK: 硬编码
    logger.info(f'Selecting character: {character}')
    if character != 'ichika':
        raise NotImplementedError('Not implemented yet.')
    for _ in Loop(interval=0.6):
        if image.find(R.Live.ChallengeLive.GroupLeoneed):
            device.click()
            logger.debug(f'Clicked group Leo/need HARDCODED.')
        elif image.find(R.Live.ChallengeLive.CharaIchika):
            device.click()
            logger.debug(f'Clicked character {character}.')
        elif image.find(R.Live.ButtonDecide):
            logger.debug('Now at song select.')
            break
    song_select()
    start_live('once')

@task('演出')
def live():
    go_home()
    solo_live()
    challenge_live('ichika')