import contextvars
from typing import Optional

from .config.base import IaaConfig
from .errors import ContextNotInitializedError

g_conf: contextvars.ContextVar[Optional[IaaConfig]] = contextvars.ContextVar('g_conf', default=None)


def init(config: IaaConfig) -> None:
    """初始化全局配置。"""
    g_conf.set(config)


def conf() -> IaaConfig:
    """获取当前上下文中的配置。"""
    config = g_conf.get()
    if config is None:
        raise ContextNotInitializedError()
    return config