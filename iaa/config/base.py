from typing import Literal
from pydantic import BaseModel

from .schemas import GameConfig, LiveConfig, SchedulerConfig


class IaaBaseTaskConfig(BaseModel):
    enabled: bool = False

class IaaConfig(BaseModel):
    name: str
    description: str
    game: GameConfig
    live: LiveConfig
    scheduler: SchedulerConfig = SchedulerConfig()