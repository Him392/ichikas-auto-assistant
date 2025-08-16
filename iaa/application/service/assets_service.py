import os.path
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .iaa_service import IaaService

class AssetsService:
    def __init__(self, iaa_service: 'IaaService'):
        self.iaa = iaa_service

    @property
    def logo_path(self) -> str:
        """一歌小助手的 LOGO 路径"""
        return os.path.join(self.iaa.root, 'assets', 'marry_with_6_mikus.png')