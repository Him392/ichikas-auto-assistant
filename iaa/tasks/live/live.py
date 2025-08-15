from typing import Literal
from typing_extensions import assert_never

from kotonebot import logging
from kotonebot import device, image, task, Loop, action, sleep, color

from iaa.tasks.live._select_song import next_song

from .. import R
from ..start_game import go_home
from ..common import at_home
from iaa.consts import PACKAGE_NAME_JP

logger = logging.getLogger(__name__)

@action('演出', screenshot_mode='manual')
def start_auto_live(
    auto_setting: Literal['all'] | Literal['once'] | int | None = 'all',
    back_to: Literal['home'] | Literal['select'] = 'home',
):
    """
    前置：位于编队界面\n
    结束：首页

    :param auto_setting: 自动演出设置。\n
        * `"all"`: 自动演出直到 AP 不足
        * 任意整数: 自动演出指定次数
        * `"once"`: 自动演出一次
        * `None`: 不自动演出
    :param back_to: 返回位置。\n
        * `"home"`: 返回首页
        * `"select"`: 返回选歌界面
    :raises NotImplementedError: 如果未实现的功能被调用。\n
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

    is_mutiple_auto = (auto_setting == 'all' or isinstance(auto_setting, int))
    for _ in Loop():
        # 结束条件
        if is_mutiple_auto:
            # 指定演出次数或直到 AP 不足
            # 结束条件是「已完成指定次数的演出」提示
            if image.find(R.Live.TextAutoLiveCompleted):
                device.click(1, 1)
                logger.info('Auto lives all completed.')
                sleep(0.3)
                break
        else:
            # 单次演出
            # 结束条件是「LIVE CLEAR」提示
            if image.find(R.Live.TextLiveClear):
                logger.debug('Waiting for LIVE CLEAR')
                break

    # 返回位置
    for _ in Loop():
        # 返回主页只要一直点就可以了
        if back_to == 'home':
            if at_home():
                break
            device.click(1, 1)
            sleep(0.6)
        # 返回选歌界面要点“返回歌曲选择”按钮
        elif back_to == 'select':
            if image.find(R.Live.ButtonGoSongSelect):
                device.click()
                logger.debug('Clicked select song button.')
                break
            device.click(1, 1)
            sleep(0.6)

@action('选歌', screenshot_mode='manual')
def enter_unit_select():
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
def solo_live(
    songs: list[str] | Literal['single-loop'] | Literal['list-loop'] | None = None
):
    """
    
    :param songs: 演出歌曲列表。\n
    * `None`: 不指定歌曲
    * `"single-loop"`: 单曲循环演出
    * `"list-loop"`: 列表循环演出
    * `list[str]`: 指定要演出的歌曲列表
    """
    # 进入单人演出
    for _ in Loop(interval=0.6):
        if image.find(R.Hud.ButtonLive, threshold=0.55):
            device.click()
            logger.debug('Clicked home LIVE button.')
            sleep(1)
        elif image.find(R.Live.ButtonSoloLive):
            device.click()
            logger.debug('Clicked SoloLive button.')
        elif image.find(R.Live.ButtonDecide):
            logger.debug('Now at song select.')
            break
    
    match songs:
        case None:
            enter_unit_select()
        case 'single-loop':
            pass
        # 列表循环
        case 'list-loop':
            for _ in Loop():
                next_song()
                enter_unit_select()
                start_auto_live('once', back_to='select')
                logger.info('Song looped.')
        case songs if isinstance(songs, list):
            raise NotImplementedError('Not implemented yet.')
        case _:
            assert_never(songs)
    start_auto_live('all')

@action('挑战演出', screenshot_mode='manual')
def challenge_live(
    character
):
    # 进入挑战演出
    for _ in Loop(interval=0.6):
        if image.find(R.Hud.ButtonLive, threshold=0.55):
            device.click()
            logger.debug('Clicked home LIVE button.')
            sleep(1)
        elif image.find(R.Live.ButtonChallengeLive):
            if not color.find('#ff5589', rect=R.Live.BoxChallengeLiveRedDot):
                logger.info("Today's challenge live already cleared.")
                return
            device.click()
            logger.debug('Clicked ChallengeLive button.')
        elif image.find(R.Live.ChallengeLive.TextSelectCharacter):
            logger.debug('Now at character select.')
            break
        elif image.find(R.Live.ChallengeLive.GroupVirtualSinger):
            # 为了防止误触某个角色，导致次数不够提示弹出来，挡住 TextSelectCharacter
            # 文本，结果一直卡在 TextSelectCharacter 识别上。
            # 加上这个点击用于取消次数不足提示。
            device.click()
            logger.debug('Clicked group virtual singer.')

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
    enter_unit_select()
    start_auto_live('once')

@task('演出')
def live():
    go_home()
    solo_live()
    challenge_live('ichika')