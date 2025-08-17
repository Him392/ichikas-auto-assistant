import os
from typing import TYPE_CHECKING

from kotonebot import logging
from iaa.config import manager
if TYPE_CHECKING:
    from .iaa_service import IaaService

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_NAME = 'default'

class ConfigService:
    def __init__(self, iaa_service: 'IaaService'):
        self.iaa = iaa_service
        manager.config_path = os.path.join(self.iaa.root, 'conf')
        self.conf = manager.read(DEFAULT_CONFIG_NAME, not_exist='create')

    def list(self) -> list[str]:
        return manager.list()

    def save(self) -> None:
        logger.info(f"Save config: {DEFAULT_CONFIG_NAME}")
        manager.write(DEFAULT_CONFIG_NAME, self.conf)