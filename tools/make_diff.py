# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "ttkbootstrap>=1.14.2",
# ]
# ///

import os
import sys
import hashlib
import zipfile
import subprocess
import threading
import queue
from dataclasses import dataclass
from typing import Literal, Optional

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, END
from tkinter.scrolledtext import ScrolledText


OutputType = Literal["zip", "7z-sfx", "7z"]


@dataclass
class DiffResult:
    base_dir: str
    new_dir: str
    files: list[str]
    total_bytes: int


def iter_files(root: str) -> list[str]:
    result: list[str] = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            if os.path.isfile(full):
                result.append(os.path.normpath(full))
    return result


def sha1_of_file(path: str, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def build_diff(old_dir: str, new_dir: str) -> DiffResult:
    old_dir = os.path.abspath(old_dir)
    new_dir = os.path.abspath(new_dir)
    old_map: dict[str, tuple[int, str]] = {}
    for f in iter_files(old_dir):
        rel = os.path.relpath(f, old_dir)
        try:
            old_map[rel] = (os.path.getsize(f), sha1_of_file(f))
        except Exception:
            continue

    changed: list[str] = []
    total = 0
    for f in iter_files(new_dir):
        rel = os.path.relpath(f, new_dir)
        size = os.path.getsize(f)
        old = old_map.get(rel)
        if old is None:
            changed.append(rel)
            total += size
        else:
            # 先比大小，不同则判为修改；大小同则校验哈希
            if old[0] != size:
                changed.append(rel)
                total += size
            else:
                try:
                    if old[1] != sha1_of_file(os.path.join(new_dir, rel)):
                        changed.append(rel)
                        total += size
                except Exception:
                    changed.append(rel)
                    total += size

    return DiffResult(base_dir=new_dir, new_dir=new_dir, files=sorted(changed), total_bytes=total)


def make_zip(diff: DiffResult, output_zip: str, log: "Logger") -> None:
    base = diff.base_dir
    os.makedirs(os.path.dirname(output_zip) or ".", exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in diff.files:
            src = os.path.join(base, rel)
            zf.write(src, rel)
            log.info(f"ZIP: add {rel}")
    log.info(f"ZIP 完成: {output_zip}")


def make_7z(diff: DiffResult, output_7z: str, seven_zip: str, log: "Logger", sfx: bool = False) -> None:
    base = diff.base_dir
    os.makedirs(os.path.dirname(output_7z) or ".", exist_ok=True)

    # 将文件列表写入临时清单
    list_path = output_7z + ".filelist.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for rel in diff.files:
            f.write(rel.replace("/", os.sep) + "\n")

    # 7z 工作目录设为 new_dir，使用相对路径以保持目录结构
    cmd = [seven_zip, "a", output_7z, f"@{os.path.basename(list_path)}"]
    log.info("运行: " + " ".join(cmd))
    try:
        subprocess.check_call(cmd, cwd=base)
    finally:
        try:
            os.remove(list_path)
        except OSError:
            pass

    if sfx:
        # 将 .7z 与 SFX 模块合并为自解压包（假设 7z.sfx 在 seven_zip 同目录）
        sfx_module = os.path.join(os.path.dirname(seven_zip), "7z.sfx")
        if not os.path.exists(sfx_module):
            raise FileNotFoundError("未找到 7z.sfx，请在 7-Zip 安装目录中确认存在")
        sfx_out = os.path.splitext(output_7z)[0] + ".exe"
        # 简单合并：copy /b 7z.sfx + config.txt + archive.7z sfx.exe
        config_path = os.path.splitext(output_7z)[0] + ".config.txt"
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(";!@Install@!UTF-8!\n")
            f.write("Title=Diff Update\n")
            f.write("GUIMode=""\n")
            f.write("RunProgram=\"cmd /c xcopy . %CD% /E /Y /I\"\n")
            f.write(";!@InstallEnd@!\n")
        log.info("生成 SFX 自解压包...")
        with open(sfx_out, "wb") as out:
            for part in (sfx_module, config_path, output_7z):
                with open(part, "rb") as p:
                    out.write(p.read())
        os.remove(config_path)
        log.info(f"SFX 完成: {sfx_out}")


class Logger:
    def __init__(self, text):
        self.text = text
        self.q: queue.Queue[str] = queue.Queue()

    def info(self, msg: str) -> None:
        self.q.put(msg)

    def error(self, msg: str) -> None:
        self.q.put("[ERROR] " + msg)

    def pump(self):
        try:
            while True:
                msg = self.q.get_nowait()
                self.text.insert(END, msg + "\n")
                self.text.see(END)
        except queue.Empty:
            pass


class App(ttk.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self.title("Diff 更新包生成器")
        self.geometry("800x540")

        self.var_old = ttk.StringVar()
        self.var_new = ttk.StringVar()
        self.var_seven = ttk.StringVar(value=self._guess_7z())
        self.var_output = ttk.StringVar()
        self.var_type = ttk.StringVar(value="zip")

        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=BOTH, expand=YES)

        # 旧目录
        self._row_dir(frm, 0, "旧版本目录", self.var_old)
        # 新目录
        self._row_dir(frm, 1, "新版本目录", self.var_new)
        # 输出类型
        ttk.Label(frm, text="输出类型").grid(row=2, column=0, sticky=W, pady=6)
        ttk.OptionMenu(frm, self.var_type, self.var_type.get(), "zip", "7z", "7z-sfx").grid(row=2, column=1, sticky=EW, pady=6)
        # 7z 路径
        self._row_file(frm, 3, "7z.exe 路径", self.var_seven, filetypes=[("7z.exe", "7z.exe"), ("All", "*.*")])
        # 输出
        self._row_file(frm, 4, "输出文件", self.var_output, save=True)

        # 动作按钮
        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=3, sticky=EW, pady=8)
        ttk.Button(btns, text="分析差异", command=self.on_analyze).pack(side=LEFT)
        ttk.Button(btns, text="生成包", command=self.on_build).pack(side=LEFT, padx=8)

        # 日志
        self.txt = ScrolledText(frm, height=14)
        self.txt.grid(row=6, column=0, columnspan=3, sticky=NSEW)
        self.logger = Logger(self.txt)
        self.after(100, self._poll_log)

        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(6, weight=1)

        self.diff: Optional[DiffResult] = None

    def _row_dir(self, parent: ttk.Frame, row: int, label: str, var: ttk.StringVar):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=W, pady=6)
        ent = ttk.Entry(parent, textvariable=var)
        ent.grid(row=row, column=1, sticky=EW)
        ttk.Button(parent, text="选择", command=lambda: var.set(filedialog.askdirectory() or var.get())).grid(row=row, column=2, padx=6)

    def _row_file(self, parent: ttk.Frame, row: int, label: str, var: ttk.StringVar, save: bool = False, filetypes=None):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=W, pady=6)
        ent = ttk.Entry(parent, textvariable=var)
        ent.grid(row=row, column=1, sticky=EW)
        def pick():
            if save:
                path = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP/7Z", "*.zip *.7z *.exe"), ("All", "*.*")])
            else:
                path = filedialog.askopenfilename(filetypes=filetypes or [("All", "*.*")])
            if path:
                var.set(path)
        ttk.Button(parent, text="选择", command=pick).grid(row=row, column=2, padx=6)

    def _poll_log(self):
        self.logger.pump()
        self.after(80, self._poll_log)

    def on_analyze(self):
        old_dir = self.var_old.get().strip()
        new_dir = self.var_new.get().strip()
        if not old_dir or not new_dir:
            messagebox.showerror("错误", "请先选择旧/新目录")
            return
        self.txt.delete("1.0", END)
        self.logger.info("开始分析差异...")

        def work():
            try:
                self.diff = build_diff(old_dir, new_dir)
                self.logger.info(f"差异文件数: {len(self.diff.files)}，总大小: {self.diff.total_bytes} 字节")
                for rel in self.diff.files:
                    self.logger.info(" - " + rel)
                if len(self.diff.files) == 0:
                    self.logger.info("没有检测到新增或修改的文件。")
            except Exception as e:
                self.logger.error(str(e))
        threading.Thread(target=work, daemon=True).start()

    def on_build(self):
        if self.diff is None:
            # 若未分析，临时建立一次
            old_dir = self.var_old.get().strip()
            new_dir = self.var_new.get().strip()
            if not old_dir or not new_dir:
                messagebox.showerror("错误", "请先选择旧/新目录")
                return
            self.diff = build_diff(old_dir, new_dir)

        typ = self.var_type.get()
        out = self.var_output.get().strip()
        if not out:
            messagebox.showerror("错误", "请先选择输出文件")
            return
        if typ == "zip" and not out.lower().endswith(".zip"):
            out += ".zip"
        if typ in ("7z", "7z-sfx") and not out.lower().endswith(".7z"):
            out += ".7z"

        self.txt.delete("1.0", END)
        self.logger.info("开始生成包...")

        def work():
            try:
                diff = self.diff
                assert diff is not None
                if typ == "zip":
                    make_zip(diff, out, self.logger)
                else:
                    seven = self.var_seven.get().strip()
                    if not seven:
                        raise RuntimeError("请先指定 7z.exe 路径")
                    make_7z(diff, out, seven, self.logger, sfx=(typ == "7z-sfx"))
                self.logger.info("完成。")
            except Exception as e:
                self.logger.error(str(e))
        threading.Thread(target=work, daemon=True).start()

    def _guess_7z(self) -> str:
        # 常见安装路径尝试
        candidates = [
            r"C:\\Program Files\\7-Zip\\7z.exe",
            r"C:\\Program Files (x86)\\7-Zip\\7z.exe",
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return ""


if __name__ == "__main__":
    app = App()
    app.mainloop() 