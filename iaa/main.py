from typing import Callable

from kotonebot import logging
from kotonebot.backend.context.context import init_context, manual_context
from kotonebot.client.host import Mumu12Host
from kotonebot.client.host.mumu12_host import MuMu12HostConfig
from kotonebot.client.implements.windows import WindowsImpl, WindowsImplConfig
from kotonebot.backend import debug

from .tasks.start_game import start_game

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s][%(levelname)s][%(name)s.%(funcName)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
TASKS: list[Callable[[], None]] = [
    start_game
]
DEBUG: bool = True

def main():
    if DEBUG:
        debug.debug.enabled = True
        debug.debug.auto_save_to_folder = 'dumps'
    ins = Mumu12Host.list()[0]
    d = ins.create_device('nemu_ipc', MuMu12HostConfig())
    init_context(target_device=d)
    for func in TASKS:
        func()

if __name__ == "__main__":
    main()
