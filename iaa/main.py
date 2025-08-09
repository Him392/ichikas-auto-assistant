import argparse
from typing import Callable

from kotonebot import logging
from kotonebot.backend.context.context import init_context, manual_context
from kotonebot.client.host import Mumu12Host
from kotonebot.client.host.mumu12_host import MuMu12HostConfig
from kotonebot.client.implements.windows import WindowsImpl, WindowsImplConfig
from kotonebot.backend import debug

from .tasks.cm import cm
from .tasks.live import live
from .tasks.start_game import start_game
from .context import init
from .config.manager import read

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s][%(levelname)s][%(name)s.%(funcName)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
TASKS: dict[str, Callable[[], None]] = {
    'start_game': start_game,
    'cm': cm,
    'live': live,
}

def main():
    parser = argparse.ArgumentParser(description='Run specific tasks')
    parser.add_argument('--task', '-t', type=str, help='Task name to run')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', '-c', type=str, default='default', help='Configuration name to use')
    args = parser.parse_args()
    
    if args.debug:
        debug.debug.enabled = True
        debug.debug.auto_save_to_folder = 'dumps'
    
    # 初始化配置
    config = read(args.config, not_exist='create')
    init(config)
    
    ins = Mumu12Host.list()[0]
    d = ins.create_device('nemu_ipc', MuMu12HostConfig())
    d.target_resolution = (1280, 720)
    d.orientation = 'landscape'
    init_context(target_device=d)
    
    if args.task:
        if args.task in TASKS:
            TASKS[args.task]()
        else:
            print(f"Available tasks: {list(TASKS.keys())}")
            print(f"Task '{args.task}' not found")
    else:
        for func in TASKS.values():
            func()

if __name__ == "__main__":
    main()
