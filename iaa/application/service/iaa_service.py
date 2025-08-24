import os
import sys
import logging
from datetime import datetime
from functools import cached_property

from .config_service import ConfigService
from .assets_service import AssetsService
from .scheduler import SchedulerService

class IaaService:
    def __init__(self):
        # 首先配置日志
        self.__configure_logging()
        
        self.config = ConfigService(self)
        self.assets = AssetsService(self)
        self.scheduler = SchedulerService(self)

    def __configure_logging(self) -> None:
        """配置日志：控制台 DEBUG + 文件 logs/YYYY-MM-DD-hh-mm-ss.log。只配置一次。"""
        root_logger = logging.getLogger()
        
        # 如果已经配置过了就跳过（避免重复配置）
        if root_logger.handlers:
            return
            
        root_logger.setLevel(logging.DEBUG)

        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)

        # 文件输出
        logs_dir = os.path.join(self.root, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        log_file_path = os.path.join(logs_dir, f'{timestamp}.log')
        file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(console_formatter)

        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

        logger = logging.getLogger(__name__)
        logger.debug("Logging configured. File: %s", log_file_path)

    @cached_property
    def root(self) -> str:
        """软件根目录。"""
        # 判断是否为打包运行
        if not os.path.basename(sys.executable).startswith('python'):
            return os.path.dirname(sys.executable)
        else:
            # 源码运行
            return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

    @cached_property
    def version(self) -> str:
        """
        软件版本号。
        若获取失败，返回 'Unknown'。
        """
        try:
            from iaa import __VERSION__  # type: ignore
            if isinstance(__VERSION__, str) and __VERSION__:
                return __VERSION__
        except Exception:
            pass
        return 'Unknown'