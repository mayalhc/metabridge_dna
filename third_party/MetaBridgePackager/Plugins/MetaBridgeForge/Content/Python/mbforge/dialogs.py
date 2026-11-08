"""tkinter-based dialogs for MetaBridge Forge.

Isolated in its own module because tkinter availability inside UE's
embedded Python was flagged as a "verify early" item during scoping - if
it turns out not to work in this project's Python build, only this file
needs a different implementation (e.g. swapping in a native unreal.py
dialog API once one is confirmed).
"""
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

# A single hidden root window, created lazily and reused - tkinter dialogs
# need a root to parent to, but we don't want a stray blank window sitting
# on screen every time a dialog opens.
_root = None


def _get_root():
    global _root
    if _root is None:
        _root = tk.Tk()
        _root.withdraw()
    return _root


def pick_fbx_file(title: str = "Select outfit FBX") -> str:
    """Returns the picked file path, or '' if the user cancelled."""
    root = _get_root()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(
        parent=root,
        title=title,
        filetypes=[("FBX files", "*.fbx"), ("All files", "*.*")],
    )
    return path or ""


def pick_abc_file(title: str = "Select groom Alembic (.abc)") -> str:
    """Returns the picked file path, or '' if the user cancelled."""
    root = _get_root()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(
        parent=root,
        title=title,
        filetypes=[("Alembic files", "*.abc"), ("All files", "*.*")],
    )
    return path or ""


def ask_outfit_name(initial: str = "", label: str = "Outfit") -> str:
    """Returns the entered name, or '' if the user cancelled.

    The name is used directly as a folder/asset name segment, so it's
    restricted to characters Unreal's Content Browser accepts. `label`
    only changes the dialog text (reused for groom names too).
    """
    root = _get_root()
    root.attributes("-topmost", True)
    name = simpledialog.askstring(
        f"{label} Name",
        f"{label} name (used for folder + asset names, e.g. BasicOutfit):",
        initialvalue=initial,
        parent=root,
    )
    if not name:
        return ""
    safe = "".join(c for c in name.strip() if c.isalnum() or c == "_")
    return safe


def show_result(title: str, text: str, is_error: bool = False) -> None:
    root = _get_root()
    root.attributes("-topmost", True)
    if is_error:
        messagebox.showerror(title, text, parent=root)
    else:
        messagebox.showinfo(title, text, parent=root)
