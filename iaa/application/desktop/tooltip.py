import tkinter as tk


class _HoverTooltip:
  """简易悬浮提示。鼠标进入 0.5 秒后显示，离开时销毁。"""

  def __init__(self, widget: tk.Misc, text: str) -> None:
    self.widget = widget
    self.text = text
    self.tip_window: tk.Toplevel | None = None
    self._after_id: str | None = None
    widget.bind("<Enter>", self._schedule_show)
    widget.bind("<Leave>", self._hide)

  def _schedule_show(self, event: tk.Event | None = None) -> None:  # noqa: ARG002
    # 进入后 0.5 秒再显示，若重复进入则重置计时
    if self.tip_window is not None:
      return
    if self._after_id is not None:
      try:
        self.widget.after_cancel(self._after_id)
      except Exception:
        pass
      self._after_id = None
    self._after_id = self.widget.after(500, self._do_show)

  def _do_show(self) -> None:
    if self.tip_window is not None:
      return
    # 使用当前鼠标全局坐标定位
    x_root = self.widget.winfo_pointerx()
    y_root = self.widget.winfo_pointery() + 20
    self.tip_window = tw = tk.Toplevel(self.widget)
    tw.wm_overrideredirect(True)
    tw.wm_geometry(f"+{x_root}+{y_root}")
    label = tk.Label(
      tw,
      text=self.text,
      justify=tk.LEFT,
      relief=tk.SOLID,
      borderwidth=1,
      background="#ffffe0",
      font=("Microsoft YaHei UI", 9),
      padx=6,
      pady=3,
    )
    label.pack()

  def _hide(self, event: tk.Event | None = None) -> None:  # noqa: ARG002
    # 退出时取消计划并关闭
    if self._after_id is not None:
      try:
        self.widget.after_cancel(self._after_id)
      except Exception:
        pass
      self._after_id = None
    if self.tip_window is not None:
      self.tip_window.destroy()
      self.tip_window = None 