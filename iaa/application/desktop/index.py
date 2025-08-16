import tkinter as tk
from dataclasses import dataclass

import ttkbootstrap as tb
from ..service.iaa_service import IaaService

@dataclass
class Store:
    var_single_live: tk.BooleanVar | None = None
    var_challenge_live: tk.BooleanVar | None = None
    var_auto_cm: tk.BooleanVar | None = None
    logo_image: tk.PhotoImage | None = None # LOGO 组件图片。防止被 GC

class DesktopApp:
    def __init__(self) -> None:
        self.root = tb.Window(themename="flatly")
        self.root.title("一歌小助手")
        self.root.geometry("900x520")
        self.store = Store()

        # 服务聚合
        self.service = IaaService()

        # Notebook 作为主容器
        self.notebook = tb.Notebook(self.root)
        self._build_tabs()
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    # -------------------- UI 构建 --------------------
    def _build_tabs(self) -> None:
        self.tab_control = tb.Frame(self.notebook)
        self.tab_settings = tb.Frame(self.notebook)
        self.tab_about = tb.Frame(self.notebook)

        self.notebook.add(self.tab_control, text="控制")
        self.notebook.add(self.tab_settings, text="配置")
        self.notebook.add(self.tab_about, text="关于")

        # 延迟导入避免循环导入
        from .tab_main import build_control_tab
        from .tab_conf import build_settings_tab
        from .tab_about import build_about_tab
        build_control_tab(self, self.tab_control)
        build_settings_tab(self, self.tab_settings)
        build_about_tab(self, self.tab_about)

    # -------------------- 事件处理 --------------------
    def on_start(self) -> None:
        selected_tasks = self._collect_selected_tasks()
        print("[启动] 选择的任务:", selected_tasks)

    def on_stop(self) -> None:
        print("[停止] 请求已发送")

    def _collect_selected_tasks(self) -> list[str]:
        tasks: list[str] = []
        if self.store.var_single_live and self.store.var_single_live.get():
            tasks.append("单人演出")
        if self.store.var_challenge_live and self.store.var_challenge_live.get():
            tasks.append("挑战演出")
        if self.store.var_auto_cm and self.store.var_auto_cm.get():
            tasks.append("自动 CM")
        return tasks

    # -------------------- 入口 --------------------
    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = DesktopApp()
    app.run()


if __name__ == "__main__":
    main()
