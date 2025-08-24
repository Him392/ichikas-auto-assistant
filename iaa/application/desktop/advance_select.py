import tkinter as tk

import ttkbootstrap as tb

from typing import Callable, Generic, Iterable, Optional, TypeVar


T = TypeVar("T")


class AdvanceSelect(tb.Frame, Generic[T]):
  def __init__(
    self,
    master: tk.Misc,
    groups: list[tuple[str, list[tuple[T, str]]]],
    selected: Optional[Iterable[T]] = None,
    mutiple: bool = False,
    placeholder: str = "请选择",
    max_dropdown_height: int = 260,
    on_change: Optional[Callable[[list[T]], None]] = None,
  ) -> None:
    super().__init__(master)
    self.groups = groups
    self.placeholder = placeholder
    self.max_dropdown_height = max_dropdown_height
    self.on_change = on_change
    self.multiple = mutiple

    self.value_to_label: dict[T, str] = {}
    self.vars: dict[T, tk.BooleanVar] = {}
    # For single-select mapping between arbitrary values and tk-compatible keys
    self.value_to_key: dict[T, str] = {}
    self.key_to_value: dict[str, T] = {}
    self.single_var: tk.StringVar = tk.StringVar(value="")
    self.single_var.trace_add("write", lambda *_args: self._on_single_change())

    # Display area (tag container + actions)
    self.display = tb.Frame(self, relief=tk.SOLID, borderwidth=1)
    self.display.pack(fill=tk.X, expand=True)
    self.display.bind("<Button-1>", self.toggle_dropdown)
    # Use grid inside display so right-side controls never get pushed out
    self.display.columnconfigure(0, weight=1)
    self.display.columnconfigure(1, weight=0)

    self.tags_frame = tb.Frame(self.display)
    self.tags_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=4)
    self.tags_frame.bind("<Button-1>", self.toggle_dropdown)
    self.placeholder_label = tb.Label(self.tags_frame, text=self.placeholder, foreground="#888888")
    self.placeholder_label.pack(side=tk.LEFT)
    self.placeholder_label.bind("<Button-1>", self.toggle_dropdown)

    right = tb.Frame(self.display)
    right.grid(row=0, column=1, padx=6)
    self.clear_btn = tb.Label(right, text="×")
    self.clear_btn.bind("<Button-1>", self.clear_selection)
    self.clear_btn.pack(side=tk.LEFT, padx=(0, 4))
    self.arrow = tb.Label(right, text="▾")
    self.arrow.pack(side=tk.LEFT)
    self.arrow.bind("<Button-1>", self.toggle_dropdown)

    self.dropdown: Optional[tk.Toplevel] = None

    # Prepare vars from groups
    idx = 0
    for _, opts in groups:
      for value, label in opts:
        self.value_to_label[value] = label
        # Key mapping for single-select radiobuttons
        key = f"k{idx}"
        self.value_to_key[value] = key
        self.key_to_value[key] = value
        idx += 1
        # BooleanVars are used for multi-select mode
        self.vars[value] = tk.BooleanVar(value=False)
        # Use default argument to capture value at definition time
        self.vars[value].trace_add("write", lambda *_args, val=value: self._on_var_change(val))

    if selected:
      if self.multiple:
        for val in selected:
          if val in self.vars:
            self.vars[val].set(True)
      else:
        for val in selected:
          if val in self.value_to_key:
            self.single_var.set(self.value_to_key[val])
            break

    self.update_display()

  def clear_selection(self, event: Optional[tk.Event] = None) -> None:  # type: ignore[override]
    if self.multiple:
      for var in self.vars.values():
        var.set(False)
    else:
      self.single_var.set("")
    self.update_display()
    if self.on_change:
      self.on_change(self.get())

  def _on_var_change(self, _value: T) -> None:
    self.update_display()
    if self.on_change:
      self.on_change(self.get())

  def _on_single_change(self) -> None:
    self.update_display()
    if self.on_change:
      self.on_change(self.get())

  def update_display(self) -> None:
    for child in self.tags_frame.winfo_children():
      # TODO: 这里要优化性能，不要每次都销毁
      child.destroy()
    if self.multiple:
      selected = [v for v, var in self.vars.items() if bool(var.get())]
      if not selected:
        self.placeholder_label = tb.Label(self.tags_frame, text=self.placeholder, foreground="#888888")
        self.placeholder_label.pack(side=tk.LEFT)
        self.placeholder_label.bind("<Button-1>", self.toggle_dropdown)
        return
      for v in selected:
        tag = tb.Frame(self.tags_frame, padding=(6, 2), relief=tk.SOLID, borderwidth=1)
        tag.pack(side=tk.LEFT, padx=4, pady=2)
        tag.bind("<Button-1>", self.toggle_dropdown)
        text_label = tb.Label(tag, text=self.value_to_label.get(v, str(v)))
        text_label.pack(side=tk.LEFT)
        text_label.bind("<Button-1>", self.toggle_dropdown)
        # Use a compact clickable label instead of a wide button to reduce size
        close_label = tb.Label(tag, text="×", padding=(2, 0), cursor="hand2")
        close_label.bind("<Button-1>", lambda _e, val=v: self._remove_value(val))
        close_label.pack(side=tk.LEFT, padx=(6, 0))
    else:
      key = self.single_var.get()
      v = self.key_to_value.get(key)
      if v is None:
        self.placeholder_label = tb.Label(self.tags_frame, text=self.placeholder, foreground="#888888")
        self.placeholder_label.pack(side=tk.LEFT)
        self.placeholder_label.bind("<Button-1>", self.toggle_dropdown)
        return
      # Single-select: only show plain text label
      text_label = tb.Label(self.tags_frame, text=self.value_to_label.get(v, str(v)))
      text_label.pack(side=tk.LEFT)
      text_label.bind("<Button-1>", self.toggle_dropdown)

  def _remove_value(self, v: T) -> None:
    if not self.multiple:
      # If removing the currently selected value in single-select, clear it
      try:
        if self.key_to_value.get(self.single_var.get()) == v:
          self.single_var.set("")
      except Exception:
        self.single_var.set("")
      return
    if v in self.vars:
      self.vars[v].set(False)

  def toggle_dropdown(self, event: Optional[tk.Event] = None) -> str:  # type: ignore[override]
    if self.dropdown and self.dropdown.winfo_exists():
      self.close_dropdown()
      return "break"
    self.open_dropdown()
    return "break"

  def open_dropdown(self) -> None:
    if self.dropdown and self.dropdown.winfo_exists():
      return
    self.dropdown = tk.Toplevel(self)
    self.dropdown.wm_overrideredirect(True)
    self.dropdown.transient(self.winfo_toplevel())
    self.dropdown.lift()
    try:
      self.dropdown.attributes("-topmost", True)
    except Exception:
      pass

    # Position just below the widget and match width
    self.update_idletasks()
    x = self.winfo_rootx()
    y = self.winfo_rooty() + self.winfo_height()
    width = max(200, self.winfo_width())
    self.dropdown.geometry(f"{width}x{self.max_dropdown_height}+{x}+{y}")

    outer = tb.Frame(self.dropdown, relief=tk.SOLID, borderwidth=1)
    outer.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(outer, highlightthickness=0, height=self.max_dropdown_height)
    vscroll = tb.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(yscrollcommand=vscroll.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vscroll.pack(side=tk.RIGHT, fill=tk.Y)

    inner = tb.Frame(canvas)
    canvas.create_window((0, 0), window=inner, anchor=tk.NW)

    def _on_inner_config(event: tk.Event) -> None:  # type: ignore[name-defined]
      canvas.configure(scrollregion=canvas.bbox("all"))

    inner.bind("<Configure>", _on_inner_config)

    # Build options grouped
    for group_name, opts in self.groups:
      tb.Label(inner, text=group_name, anchor=tk.W).pack(fill=tk.X, padx=10, pady=(8, 4))
      row = tb.Frame(inner)
      row.pack(fill=tk.X, padx=12, pady=2)
      for value, label in opts:
        if self.multiple:
          tb.Checkbutton(row, text=label, variable=self.vars[value]).pack(side=tk.LEFT, padx=(0, 12))
        else:
          tb.Radiobutton(row, text=label, variable=self.single_var, value=self.value_to_key[value]).pack(side=tk.LEFT, padx=(0, 12))

    # Mouse wheel scrolling support: bind on dropdown widgets (Windows/macOS/Linux)
    def _on_mousewheel(event: tk.Event) -> None:  # type: ignore[name-defined]
      try:
        if hasattr(event, "delta") and event.delta != 0:
          canvas.yview_scroll(int(-event.delta / 120), "units")
        elif getattr(event, "num", None) == 4:
          canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
          canvas.yview_scroll(1, "units")
      except Exception:
        pass

    for w in (self.dropdown, outer, canvas, inner):
      if w is not None:
        try:
          w.bind("<MouseWheel>", _on_mousewheel, add="+")
          w.bind("<Button-4>", _on_mousewheel, add="+")
          w.bind("<Button-5>", _on_mousewheel, add="+")
        except Exception:
          pass

    # Auto-close behaviors (delay to avoid capturing the same click)
    dd = self.dropdown
    if dd is not None:
      self.after(0, lambda d=dd: d.focus_force())
      self.after(10, lambda: self.bind_all("<Button-1>", self._handle_global_click, add="+"))

  def _handle_global_click(self, event: tk.Event) -> None:  # type: ignore[name-defined]
    if not self.dropdown:
      return
    w = event.widget
    if self._is_ancestor(w, self.display) or self._is_ancestor(w, self.dropdown):
      return
    self.close_dropdown()

  def _is_ancestor(self, widget: Optional[tk.Misc], ancestor: Optional[tk.Misc]) -> bool:
    if ancestor is None:
      return False
    try:
      current: Optional[tk.Misc] = widget
      while current is not None:
        if current == ancestor:
          return True
        current = current.master  # type: ignore[assignment]
    except Exception:
      return False
    return False

  def close_dropdown(self) -> None:
    if self.dropdown:
      try:
        self.unbind_all("<Button-1>")
      except Exception:
        pass
      self.dropdown.destroy()
      self.dropdown = None

  def get(self) -> list[T]:
    if self.multiple:
      return [v for v, var in self.vars.items() if bool(var.get())]
    key = self.single_var.get()
    v = self.key_to_value.get(key)
    return [v] if v is not None else []

  def set(self, values: Iterable[T]) -> None:
    if self.multiple:
      value_set = set(values)
      for v, var in self.vars.items():
        var.set(v in value_set)
      self.update_display()
      return
    # Single-select: set first value only
    first: Optional[T] = None
    for first in values:
      break
    if first is not None and first in self.value_to_key:
      self.single_var.set(self.value_to_key[first])
    else:
      self.single_var.set("")
    self.update_display()
