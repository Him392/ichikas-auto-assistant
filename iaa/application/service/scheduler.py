﻿import time
import logging
import threading
import os
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .iaa_service import IaaService

from iaa.tasks.registry import REGULAR_TASKS, name_from_id
from iaa.tasks.registry import MANUAL_TASKS
from iaa.context import init as init_config_context

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self, iaa_service: 'IaaService'):
        self.iaa = iaa_service
        self._thread: threading.Thread | None = None
        self.__running: bool = False
        self.__stop_requested: bool = False
        self.is_starting: bool = False
        """是否正在启动"""
        self.is_stopping: bool = False
        """是否正在停止"""
        self.on_error: Callable[[Exception], None] | None = None
        """
        任务发生错误时执行的回调函数。注意，调用可能来自其他线程。
        
        仅在异步执行任务时有效。同步执行任务可自行 try-except。
        """
        self.current_task_id: str | None = None
        """当前正在执行的任务 ID"""
        self.current_task_name: str | None = None
        """当前正在执行的任务名称"""

    @property
    def running(self) -> bool:
        """调度器是否正在运行。"""
        return self.__running

    # -------------------- Shared runner --------------------
    def __start_tasks(
        self,
        get_tasks: Callable[[], list[tuple[str, Callable[[], None]]]],
        *,
        thread_name: str,
        run_in_thread: bool = True,
    ) -> None:
        """执行指定任务"""
        # 已在运行则忽略
        if self._thread and self._thread.is_alive():
            logger.warning("Scheduler already running, skip start.")
            return

        self.is_starting = True

        def _runner() -> None:
            try:
                logger.info("Preparing context...")
                self.__prepare_context()
                logger.info("Scheduler started.")
                tasks = get_tasks()
                if not tasks:
                    logger.info("No tasks to run. Exiting...")
                    return
                self.__running = True
                # 启动阶段结束
                self.is_starting = False
                for task_id, func in tasks:
                    self.current_task_id = task_id
                    self.current_task_name = name_from_id(task_id)
                    try:
                        logger.info(f"Running task: {task_id} ({self.current_task_name})")
                        func()
                        logger.info(f"Task finished: {task_id} ({self.current_task_name})")
                    except KeyboardInterrupt:
                        logger.info("KeyboardInterrupt received. Stopping scheduler.")
                        break
                    except Exception as e:  # noqa: BLE001
                        logger.exception(f"Task '{task_id}' raised an exception: {e}")
                        if self.on_error:
                            try:
                                self.on_error(e)
                            except Exception:
                                logger.exception("Error handler raised an exception")
                    finally:
                        self.current_task_id = None
                        self.current_task_name = None
            except Exception as e:  # noqa: BLE001
                logger.exception("Scheduler runner crashed: %s", e)
                if self.on_error:
                    try:
                        self.on_error(e)
                    except Exception:
                        logger.exception("Error handler raised an exception")
            finally:
                self.__running = False
                # 停止阶段结束
                if self.__stop_requested:
                    self.is_stopping = False
                    self.__stop_requested = False
                from kotonebot.backend.context import vars
                vars.flow.clear_interrupt()
                # 若在准备阶段失败，也需要复位启动标记
                self.is_starting = False
                logger.info("Scheduler stopped.")

        if run_in_thread:
            self._thread = threading.Thread(target=_runner, name=thread_name, daemon=True)
            self._thread.start()
        else:
            _runner()

    def start_regular(self, run_in_thread: bool = True) -> None:
        """
        启动常规任务调度。
        """
        def _get() -> list[tuple[str, Callable[[], None]]]:
            return self._get_enabled_tasks()
        self.__start_tasks(_get, thread_name="IAA-Scheduler", run_in_thread=run_in_thread)
    
    def stop(self, block: bool = False) -> None:
        """
        请求停止任务执行并回收线程。

        :param block: 是否阻塞直至线程停止。
        """
        if not self.__running or self._thread is None:
            logger.warning("Scheduler not running, skip stop.")
            return
        from kotonebot.backend.context import vars
        self.__stop_requested = True
        self.is_stopping = True
        vars.flow.request_interrupt()
        if block:
            self._thread.join()
        self._thread = None

    def run_manual(self, task_id: str, run_in_thread: bool = True) -> None:
        """运行手动任务。"""
        if task_id not in MANUAL_TASKS:
            raise ValueError(f"Unknown manual task: {task_id}")
        def _get() -> list[tuple[str, Callable[[], None]]]:
            return [(task_id, MANUAL_TASKS[task_id])]
        self.__start_tasks(_get, thread_name="IAA-Scheduler-Manual", run_in_thread=run_in_thread)

    def __prepare_context(self) -> None:
        """
        初始化配置上下文与设备上下文。

        .. NOTE::
            需要和任务执行在同一个线程中调用。
        """
        # 因为导入 kotonebot 开销较大，这里延迟导入
        from kotonebot.backend.context.context import init_context
        from kotonebot.client.host import Mumu12Host
        impl = self.iaa.config.conf.game.control_impl

        hosts = Mumu12Host.list()
        if not hosts:
            raise RuntimeError("No MuMu host found.")
        host = hosts[0]
        if impl == 'nemu_ipc':
            from kotonebot.client.host.mumu12_host import MuMu12HostConfig
            device = host.create_device('nemu_ipc', MuMu12HostConfig())
        elif impl == 'adb':
            from kotonebot.client.host import AdbHostConfig
            device = host.create_device('adb', AdbHostConfig())
        else:
            raise ValueError(f"Unknown control implementation: {impl}")
        device.target_resolution = (1280, 720)
        device.orientation = 'landscape'
        init_context(target_device=device)

        init_config_context(self.iaa.config.conf)

    def _get_enabled_tasks(self) -> list[tuple[str, Callable[[], None]]]:
        """根据配置返回启用的任务列表，顺序与 REGULAR_TASKS 保持一致。"""
        conf = self.iaa.config.conf
        tasks: list[tuple[str, Callable[[], None]]] = []
        for name, func in REGULAR_TASKS.items():
            if conf.scheduler.is_enabled(name):
                tasks.append((name, func))
        return tasks
