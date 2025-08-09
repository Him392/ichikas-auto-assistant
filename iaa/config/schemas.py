from typing import Literal
from pydantic import BaseModel

LinkAccountOptions = Literal['google_play']

class GameConfig(BaseModel):
    server: Literal['jp'] = 'jp'
    link_account: None | LinkAccountOptions = None
    """
    是否引继账号。
    
    * `None`： 不引继账号
    * `"google_play"`： 引继 Google Play 账号
    """


class LiveConfig(BaseModel):
    enabled: bool = False
    mode: Literal['auto'] = 'auto'
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