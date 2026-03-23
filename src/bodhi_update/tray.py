"""GTK StatusIcon tray companion for Bodhi Update Manager.

Provides a lightweight system tray icon with a right-click menu.
No polling, no daemon, no background refresh — manual launch only.
"""

from __future__ import annotations

import os
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402


# Path to the main launcher, resolvable both from source tree and installed.
_LAUNCHER = "/usr/bin/bodhi-update-manager"


def _open_update_manager() -> None:
    """Spawn the main Bodhi Update Manager window."""
    # Prefer the installed launcher; fall back to running as a module
    # so the tray is usable directly from the source tree.
    if os.path.isfile(_LAUNCHER):
        argv = [_LAUNCHER]
    else:
        argv = [sys.executable, "-m", "bodhi_update.app"]
    try:
        subprocess.Popen(argv)
    except OSError as exc:
        _show_error(f"Could not launch Bodhi Update Manager:\n{exc}")


def _show_error(msg: str) -> None:
    dialog = Gtk.MessageDialog(
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.CLOSE,
        text=msg,
    )
    dialog.run()
    dialog.destroy()


def _build_menu() -> Gtk.Menu:
    menu = Gtk.Menu()

    open_item = Gtk.MenuItem(label="Open Update Manager")
    open_item.connect("activate", lambda _: _open_update_manager())
    menu.append(open_item)

    menu.append(Gtk.SeparatorMenuItem())

    quit_item = Gtk.MenuItem(label="Quit")
    quit_item.connect("activate", lambda _: Gtk.main_quit())
    menu.append(quit_item)

    menu.show_all()
    return menu


def main() -> None:
    icon = Gtk.StatusIcon()
    icon.set_from_icon_name("bodhi-update-manager")
    icon.set_tooltip_text("Bodhi Update Manager")
    icon.set_visible(True)

    menu = _build_menu()

    # Left-click: open the main app.
    icon.connect("activate", lambda _: _open_update_manager())

    # Right-click: show the context menu.
    def on_popup(status_icon: Gtk.StatusIcon, button: int, time: int) -> None:
        menu.popup(None, None, Gtk.StatusIcon.position_menu, status_icon, button, time)

    icon.connect("popup-menu", on_popup)

    Gtk.main()


if __name__ == "__main__":
    main()
