import argparse

from kotonebot.backend import debug

from iaa.application.service.iaa_service import IaaService
from iaa.tasks.registry import MANUAL_TASKS, REGULAR_TASKS
import iaa.application.service.config_service as config_service_module


def main():
    parser = argparse.ArgumentParser(description='Run specific tasks')
    parser.add_argument('--task', '-t', type=str, help='Task name to run')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', '-c', type=str, default='default', help='Configuration name to use')
    args = parser.parse_args()

    if args.debug:
        debug.debug.enabled = True
        debug.debug.auto_save_to_folder = 'dumps'

    # 覆盖配置名称后再构造服务，确保 ConfigService 读取目标配置
    config_service_module.DEFAULT_CONFIG_NAME = args.config

    # 初始化核心服务（日志、配置、资源、调度器）
    iaa = IaaService()

    if args.task:
        try:
            # 同步执行单个手动任务
            iaa.scheduler.run_single(args.task, run_in_thread=False)
        except ValueError:
            print(f"Available tasks: {list(MANUAL_TASKS.keys())}")
            print(f"Task '{args.task}' not found")
    else:
        # 同步执行按配置启用的常规任务
        iaa.scheduler.start_regular(run_in_thread=False)


if __name__ == "__main__":
    main()
