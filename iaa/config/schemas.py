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
    start_game_enabled: bool = True
    solo_live_enabled: bool = True
    challenge_live_enabled: bool = True
    cm_enabled: bool = True

    def is_enabled(self, task_id: str) -> bool:
        """根据任务标识判断是否启用。
        
        任务标识应与 `iaa.tasks.registry.REGULAR_TASKS` 的键一致，例如：
        - "start_game"
        - "cm"
        - "solo_live"
        - "challenge_live"
        """
        if task_id == 'start_game':
            return bool(self.start_game_enabled)
        if task_id == 'cm':
            return bool(self.cm_enabled)
        if task_id == 'solo_live':
            return bool(self.solo_live_enabled)
        if task_id == 'challenge_live':
            return bool(self.challenge_live_enabled)
        return False