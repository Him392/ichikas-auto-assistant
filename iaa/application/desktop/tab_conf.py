import tkinter as tk

import ttkbootstrap as tb

from .index import DesktopApp
from typing import cast, Literal, Optional
from iaa.config.schemas import LinkAccountOptions, EmulatorOptions, GameCharacter
from .toast import show_toast
from .advance_select import AdvanceSelect
from iaa.config.base import IaaConfig


class ConfStore:
  def __init__(self):
    # 游戏设置
    self.emulator_var = tk.StringVar()
    self.server_var = tk.StringVar()
    self.link_var = tk.StringVar()
    # 演出设置
    self.song_var = tk.StringVar()
    self.fully_deplete_var = tk.BooleanVar()
    # 挑战演出设置
    self.challenge_char_vars: dict[GameCharacter, tk.BooleanVar] = {}
    # 分组多选组件实例
    self.challenge_select: Optional[AdvanceSelect[GameCharacter]] = None
    # 映射表
    self.emulator_value_map: dict[str, str] = {}
    self.server_value_map: dict[str, str] = {}
    self.link_value_map: dict[str, LinkAccountOptions] = {}
    self.song_display_to_value: dict[str, int] = {}


def build_game_config_group(parent: tk.Misc, conf: IaaConfig, store: ConfStore) -> None:
  # 显示映射
  emulator_display_map = {
    'mumu': 'MuMu',
  }
  server_display_map = {
    'jp': '日服',
  }
  link_display_map = {
    'no': '不引继账号',
    'google_play': 'Google Play',
  }
  store.emulator_value_map = {v: k for k, v in emulator_display_map.items()}
  store.server_value_map = {v: k for k, v in server_display_map.items()}
  store.link_value_map = {v: cast(LinkAccountOptions, k) for k, v in link_display_map.items()}

  frame = tb.Labelframe(parent, text="游戏设置")
  frame.pack(fill=tk.X, padx=16, pady=8)

  # 初始化变量
  emulator_key = conf.game.emulator
  server_key = conf.game.server
  link_key = conf.game.link_account
  store.emulator_var.set(emulator_display_map.get(emulator_key, 'MuMu'))
  store.server_var.set(server_display_map.get(server_key, '日服'))
  store.link_var.set(link_display_map.get(link_key, '不引继账号'))

  # 模拟器类型
  row = tb.Frame(frame)
  row.pack(fill=tk.X, padx=8, pady=8)
  tb.Label(row, text="模拟器类型", width=16, anchor=tk.W).pack(side=tk.LEFT)
  tb.Combobox(row, state="readonly", textvariable=store.emulator_var, values=list(store.emulator_value_map.keys()), width=28).pack(side=tk.LEFT)

  # 服务器
  row = tb.Frame(frame)
  row.pack(fill=tk.X, padx=8, pady=8)
  tb.Label(row, text="服务器", width=16, anchor=tk.W).pack(side=tk.LEFT)
  tb.Combobox(row, state="readonly", textvariable=store.server_var, values=list(store.server_value_map.keys()), width=28).pack(side=tk.LEFT)

  # 引继账号
  row = tb.Frame(frame)
  row.pack(fill=tk.X, padx=8, pady=8)
  tb.Label(row, text="引继账号", width=16, anchor=tk.W).pack(side=tk.LEFT)
  tb.Combobox(row, state="readonly", textvariable=store.link_var, values=list(store.link_value_map.keys()), width=28).pack(side=tk.LEFT)


def build_live_config_group(parent: tk.Misc, conf: IaaConfig, store: ConfStore) -> None:
  frame = tb.Labelframe(parent, text="演出设置")
  frame.pack(fill=tk.X, padx=16, pady=8)

  # 歌曲映射
  song_value_to_display = {
    -1: '保持不变',
    1: 'Tell Your World｜Tell Your World',
    47: 'メルト｜Melt',
    74: '独りんぼエンヴィー｜孑然妒火',
  }
  store.song_display_to_value = {v: k for k, v in song_value_to_display.items()}

  song_id = conf.live.song_id
  current_song_display = song_value_to_display[song_id] if isinstance(song_id, int) and song_id in song_value_to_display else '保持不变'
  store.song_var.set(current_song_display)
  store.fully_deplete_var.set(bool(conf.live.fully_deplete))

  # 歌曲下拉
  row = tb.Frame(frame)
  row.pack(fill=tk.X, padx=8, pady=8)
  tb.Label(row, text="歌曲", width=16, anchor=tk.W).pack(side=tk.LEFT)
  tb.Combobox(row, state="disabled", textvariable=store.song_var, values=list(store.song_display_to_value.keys()), width=28).pack(side=tk.LEFT)

  # 完全清空体力
  row = tb.Frame(frame)
  row.pack(fill=tk.X, padx=8, pady=8)
  tb.Checkbutton(row, text="完全清空体力", variable=store.fully_deplete_var, state="disabled").pack(side=tk.LEFT)


def build_challenge_live_config_group(parent: tk.Misc, conf: IaaConfig, store: ConfStore) -> None:
  frame = tb.Labelframe(parent, text="挑战演出设置")
  frame.pack(fill=tk.X, padx=16, pady=8)

  # 分组到角色列表
  groups: list[tuple[str, list[GameCharacter]]] = [
    ("VIRTUAL SINGER", [
      GameCharacter.Miku, GameCharacter.Rin, GameCharacter.Len,
      GameCharacter.Luka, GameCharacter.Meiko, GameCharacter.Kaito,
    ]),
    ("Leo/need", [GameCharacter.Ichika, GameCharacter.Saki, GameCharacter.Honami, GameCharacter.Shiho]),
    ("MORE MORE JUMP!", [GameCharacter.Minori, GameCharacter.Haruka, GameCharacter.Airi, GameCharacter.Shizuku]),
    ("Vivid BAD SQUAD", [GameCharacter.Kohane, GameCharacter.An, GameCharacter.Akito, GameCharacter.Toya]),
    ("ワンダーランズ×ショウタイム", [GameCharacter.Tsukasa, GameCharacter.Emu, GameCharacter.Nene, GameCharacter.Rui]),
    ("25時、ナイトコードで。", [GameCharacter.Kanade, GameCharacter.Mafuyu, GameCharacter.Ena, GameCharacter.Mizuki]),
  ]

  selected: list[GameCharacter] = list(conf.challenge_live.characters)

  row = tb.Frame(frame)
  row.pack(fill=tk.X, padx=8, pady=8)
  tb.Label(row, text="角色", width=16, anchor=tk.W).pack(side=tk.LEFT)
  grouped_options: list[tuple[str, list[tuple[GameCharacter, str]]]] = [
    (name, [(ch, ch.last_name_cn +ch.first_name_cn) for ch in chars]) for name, chars in groups
  ]
  select = AdvanceSelect[GameCharacter](row, groups=grouped_options, selected=selected, mutiple=False, placeholder="请选择角色")
  select.pack(side=tk.LEFT, fill=tk.X, expand=True)
  store.challenge_select = select


def build_settings_tab(app: DesktopApp, parent: tk.Misc) -> None:  # noqa: ARG001
  # 可滚动容器
  container = tb.Frame(parent)
  container.pack(fill=tk.BOTH, expand=True)

  canvas = tk.Canvas(container, highlightthickness=0)
  vscroll = tb.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
  canvas.configure(yscrollcommand=vscroll.set)

  inner = tb.Frame(canvas)
  inner_id = canvas.create_window((0, 0), window=inner, anchor=tk.NW)

  def _on_inner_config(event: tk.Event) -> None:  # type: ignore[name-defined]
    canvas.configure(scrollregion=canvas.bbox("all"))

  def _on_canvas_config(event: tk.Event) -> None:  # type: ignore[name-defined]
    canvas.itemconfigure(inner_id, width=canvas.winfo_width())

  inner.bind("<Configure>", _on_inner_config)
  canvas.bind("<Configure>", _on_canvas_config)

  # 鼠标滚轮（限制顶部/底部不超出）
  def _on_mousewheel(event: tk.Event):  # type: ignore[name-defined]
    first, last = canvas.yview()
    if event.delta > 0 and first <= 0:
      return "break"
    if event.delta < 0 and last >= 1:
      return "break"
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    return "break"

  # Linux 鼠标滚轮
  def _on_mousewheel_up(event: tk.Event):  # type: ignore[name-defined]
    first, _ = canvas.yview()
    if first <= 0:
      return "break"
    canvas.yview_scroll(-1, "units")
    return "break"

  def _on_mousewheel_down(event: tk.Event):  # type: ignore[name-defined]
    _, last = canvas.yview()
    if last >= 1:
      return "break"
    canvas.yview_scroll(1, "units")
    return "break"

  def _bind_mousewheel(event: tk.Event) -> None:  # type: ignore[name-defined]
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    canvas.bind_all("<Button-4>", _on_mousewheel_up)
    canvas.bind_all("<Button-5>", _on_mousewheel_down)

  def _unbind_mousewheel(event: tk.Event) -> None:  # type: ignore[name-defined]
    canvas.unbind_all("<MouseWheel>")
    canvas.unbind_all("<Button-4>")
    canvas.unbind_all("<Button-5>")

  canvas.bind("<Enter>", _bind_mousewheel)
  canvas.bind("<Leave>", _unbind_mousewheel)

  canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
  vscroll.pack(side=tk.RIGHT, fill=tk.Y)

  # 当前配置
  conf = app.service.config.conf

  # 顶部操作区：保存
  actions = tb.Frame(inner)
  actions.pack(fill=tk.X, padx=16, pady=(16, 8))

  # Store
  store = ConfStore()

  # 分组构建
  build_game_config_group(inner, conf, store)
  build_live_config_group(inner, conf, store)
  build_challenge_live_config_group(inner, conf, store)

  def on_save() -> None:
    try:
      # 游戏设置
      emulator_val = cast(EmulatorOptions, store.emulator_value_map[store.emulator_var.get()])
      server_val = cast(Literal['jp'], store.server_value_map[store.server_var.get()])
      link_val = cast(LinkAccountOptions, store.link_value_map[store.link_var.get()])
      conf.game.emulator = emulator_val
      conf.game.server = server_val
      conf.game.link_account = link_val

      # 演出设置
      song_display = store.song_var.get()
      conf.live.song_id = store.song_display_to_value.get(song_display, -1)
      conf.live.fully_deplete = bool(store.fully_deplete_var.get())

      # 挑战演出设置
      selected_chars: list[GameCharacter] = store.challenge_select.get() if store.challenge_select else []
      conf.challenge_live.characters = selected_chars

      app.service.config.save()
      show_toast(app.root, "保存成功", kind="success")
    except Exception as e:
      show_toast(app.root, f"保存失败：{e}", kind="danger")

  tb.Button(actions, text="保存", command=on_save).pack(anchor=tk.W)