import os
import sys
from functools import cached_property

from .config_service import ConfigService
from .assets_service import AssetsService

class IaaService:
    def __init__(self):
        self.config = ConfigService(self)
        self.assets = AssetsService(self)

    @cached_property
    def root(self) -> str:
        """软件根目录。"""
        # 判断是否为打包运行
        if not os.path.basename(sys.executable).startswith('python'):
            return os.path.dirname(sys.executable)
        else:
            # 源码运行
            return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

    @property
    def version(self) -> str:
        return 'Not implemented yet.'