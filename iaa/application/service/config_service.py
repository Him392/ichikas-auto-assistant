import os
from typing import TYPE_CHECKING

from iaa.config import manager
if TYPE_CHECKING:
    from .iaa_service import IaaService

DEFAULT_CONFIG_NAME = 'default'

class ConfigService:
    def __init__(self, iaa_service: 'IaaService'):
        self.iaa = iaa_service
        manager.config_path = os.path.join(self.iaa.root, 'conf')
        self.conf = manager.read(DEFAULT_CONFIG_NAME, not_exist='create')

    def list(self) -> list[str]:
        return manager.list()

    def save(self) -> None:
        manager.write(DEFAULT_CONFIG_NAME, self.conf)