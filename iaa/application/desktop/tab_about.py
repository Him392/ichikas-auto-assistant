import webbrowser
import tkinter as tk

import ttkbootstrap as tb

from .index import DesktopApp
from .tooltip import _HoverTooltip

def build_about_tab(app: DesktopApp, parent: tk.Misc) -> None:
  # 外层容器，整体居中
  container = tb.Frame(parent)
  container.pack(fill=tk.BOTH, expand=True)

  inner = tb.Frame(container)
  inner.pack(expand=True)  # 在父容器中水平垂直居中

  # LOGO
  try:
    app.store.logo_image = tk.PhotoImage(file=app.service.assets.logo_path)
    logo_label = tk.Label(inner, image=app.store.logo_image)
    logo_label.pack(pady=(20, 8))
    _HoverTooltip(logo_label, "我同时和六个初音未来结婚")
  except Exception:
    # 找不到或加载失败时忽略
    pass

  # 标题与版本
  title = tb.Label(inner, text="一歌小助手 iaa", font=("Microsoft YaHei UI", 20, "bold"))
  subtitle = tb.Label(inner, text=f"版本 v{app.service.version}", font=("Microsoft YaHei UI", 10))
  title.pack(pady=(0, 6))
  subtitle.pack(pady=(0, 12))

  # 链接横向排布
  links = tb.Frame(inner)
  links.pack()

  def add_link(parent_frame: tk.Misc, text: str, url: str) -> None:
    lbl = tk.Label(parent_frame, text=text, fg="#0d6efd", cursor="hand2", font=("Microsoft YaHei UI", 10, "underline"))
    lbl.pack(side=tk.LEFT, padx=10)
    lbl.bind("<Button-1>", lambda e: webbrowser.open(url))  # noqa: ARG005

  add_link(links, "GitHub", "https://github.com/XcantloadX/ichikas-auto-assistant")
  add_link(links, "Bilibili", "https://space.bilibili.com/3546853903698457")
  add_link(links, "教程文档", "https://p.kdocs.cn/s/AGBH56RBAAAFS")
  add_link(links, "QQ 群", "https://qm.qq.com/q/Mu1SSfK1Gg") 