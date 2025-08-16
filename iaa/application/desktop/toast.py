import tkinter as tk


def show_toast(parent: tk.Misc, message: str, title: str = "提示", duration_ms: int = 2000, kind: str = "info") -> None:
  """显示简易 toast 提示（顶部居中、带边框、按类型着色）。

  :param parent: 关联父级窗口（用于定位）
  :param message: 显示文案
  :param title: 标题
  :param duration_ms: 显示时长（毫秒）
  :param kind: 颜色风格：info/success/warning/danger
  """
  root = parent.winfo_toplevel()

  # 配色方案（背景/前景）
  palette: dict[str, tuple[str, str]] = {
    "info": ("#e8f4fd", "#0c5460"),
    "success": ("#d1e7dd", "#0f5132"),
    "warning": ("#fff3cd", "#664d03"),
    "danger": ("#f8d7da", "#842029"),
  }
  bg, fg = palette.get(kind, palette["info"])  # 默认 info

  win = tk.Toplevel(root)
  win.overrideredirect(True)
  win.attributes("-topmost", True)
  win.configure(bg=bg)

  # 容器与样式（带边框）
  padding = 12
  border_color = "#dee2e6"  # 淡灰色边框
  frame = tk.Frame(win, bg=bg, bd=1, relief=tk.SOLID, highlightthickness=1, highlightbackground=border_color)
  frame.pack(fill=tk.BOTH, expand=True)

  title_lbl = tk.Label(frame, text=title, font=("Segoe UI", 10, "bold"), bg=bg, fg=fg)
  title_lbl.pack(anchor=tk.W, padx=padding, pady=(padding, 0))

  msg_lbl = tk.Label(frame, text=message, bg=bg, fg=fg, wraplength=360, justify=tk.LEFT)
  msg_lbl.pack(anchor=tk.W, padx=padding, pady=(6, padding))

  win.update_idletasks()

  # 顶部居中定位
  parent_x = root.winfo_rootx()
  parent_y = root.winfo_rooty()
  parent_w = root.winfo_width()
  win_w = win.winfo_reqwidth()
  win_h = win.winfo_reqheight()

  margin = 16
  x = parent_x + (parent_w - win_w) // 2
  y = parent_y + margin
  win.geometry(f"{win_w}x{win_h}+{x}+{y}")

  # 自动关闭
  win.after(duration_ms, win.destroy) 