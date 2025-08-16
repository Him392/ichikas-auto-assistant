from typing import Literal
from pydantic import BaseModel

LinkAccountOptions = Literal['no', 'google_play']
EmulatorOptions = Literal['mumu']

class GameConfig(BaseModel):
    server: Literal['jp'] = 'jp'
    link_account: LinkAccountOptions = 'no'
    emulator: EmulatorOptions = 'mumu'
    """
    是否引继账号。
    
    * `"no"`： 不引继账号
    * `"google_play"`： 引继 Google Play 账号
    """


class LiveConfig(BaseModel):
    enabled: bool = False
    mode: Literal['auto'] = 'auto'
    song_id: int = -1
    count_mode: Literal['once', 'all', 'specify'] = 'all'
    """
    演出次数模式。

    * `"once"`： 一次。
    * `"all"`： 直到 AP 不足。
    * `"specify"`： 指定次数。
    """
    count: int | None = None
    """
    指定次数。
    """
    fully_deplete: bool = False


class SchedulerConfig(BaseModel):
    solo_live_enabled: bool = False
    challenge_live_enabled: bool = False
    cm_enabled: bool = False