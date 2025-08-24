﻿from typing import Callable

from .cm import cm
from .live import challenge_live, solo_live
from .live.ten_songs import ten_songs
from .start_game import start_game

TaskRegistry = dict[str, Callable[[], None]]

REGULAR_TASKS: TaskRegistry = {
    'start_game': start_game,
    'cm': cm,
    'solo_live': solo_live,
    'challenge_live': challenge_live,
}

MANUAL_TASKS: TaskRegistry = {
    'ten_songs': ten_songs,
}


def name_from_id(task_id: str) -> str:
  """根据任务 id 返回可读名称。未知 id 返回原值。"""
  mapping: dict[str, str] = {
    'start_game': '启动游戏',
    'cm': '自动 CM',
    'solo_live': '单人演出',
    'challenge_live': '挑战演出',
    'ten_songs': '刷歌曲首数',
  }
  return mapping.get(task_id, task_id)