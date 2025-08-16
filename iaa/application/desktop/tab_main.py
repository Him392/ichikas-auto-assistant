import tkinter as tk

import ttkbootstrap as tb

from .index import DesktopApp

def build_control_tab(app: DesktopApp, parent: tk.Misc) -> None:
  # 启停区域
  lf_power = tb.Labelframe(parent, text="启停")
  lf_power.pack(fill=tk.X, padx=8, pady=(8, 12))

  btn_start = tb.Button(
    lf_power,
    text="启动",
    bootstyle="success",  # type: ignore[call-arg]
    width=10,
    command=app.on_start,
  )
  btn_stop = tb.Button(
    lf_power,
    text="停止",
    bootstyle="danger",  # type: ignore[call-arg]
    width=10,
    command=app.on_stop,
  )
  btn_start.pack(side=tk.LEFT, padx=(12, 8), pady=10)
  btn_stop.pack(side=tk.LEFT, padx=8, pady=10)

  # 任务区域
  lf_tasks = tb.Labelframe(parent, text="任务")
  lf_tasks.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

  # 采用 grid 简单排版
  conf = app.service.config.conf
  var_single_live = tk.BooleanVar(value=bool(conf.scheduler.solo_live_enabled))
  var_challenge_live = tk.BooleanVar(value=bool(conf.scheduler.challenge_live_enabled))
  var_auto_cm = tk.BooleanVar(value=bool(conf.scheduler.cm_enabled))
  app.store.var_single_live = var_single_live
  app.store.var_challenge_live = var_challenge_live
  app.store.var_auto_cm = var_auto_cm

  def _save_scheduler() -> None:
    conf.scheduler.solo_live_enabled = bool(var_single_live.get())
    conf.scheduler.challenge_live_enabled = bool(var_challenge_live.get())
    conf.scheduler.cm_enabled = bool(var_auto_cm.get())
    app.service.config.save()

  cb_single = tb.Checkbutton(lf_tasks, text="单人演出", variable=var_single_live, command=_save_scheduler)
  cb_challenge = tb.Checkbutton(lf_tasks, text="挑战演出", variable=var_challenge_live, command=_save_scheduler)
  cb_cm = tb.Checkbutton(lf_tasks, text="自动 CM", variable=var_auto_cm, command=_save_scheduler)

  cb_single.grid(row=0, column=0, sticky=tk.W, padx=20, pady=(16, 8))
  cb_challenge.grid(row=0, column=1, sticky=tk.W, padx=40, pady=(16, 8))
  cb_cm.grid(row=0, column=2, sticky=tk.W, padx=40, pady=(16, 8))

  # 让容器在放大时保留边距
  lf_tasks.grid_columnconfigure(3, weight=1) 