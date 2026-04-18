""" Dialogs used by the class UpdateManagerApplication. """

from __future__ import annotations

from gettext import gettext as _
from typing import Dict, List, Tuple

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class PreferencesDialog(Gtk.Dialog):
    """Preferences dialog for Bodhi Update Manager."""

    def __init__(
        self,
        parent: Gtk.Window,
        *,
        title: str,
        notifications_label: str,
        held_label: str,
        cancel_label: str,
        apply_label: str,
        show_notifications: bool,
        show_held_packages: bool,
        backend_states: List[Tuple[str, str, bool]],
    ) -> None:
        """
        backend_states:
            List of tuples:
            (backend_id, display_label, is_enabled)
        """
        super().__init__(
            title=title,
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL,
        )

        self.add_button(cancel_label, Gtk.ResponseType.CANCEL)
        self.add_button(apply_label, Gtk.ResponseType.APPLY)

        self._backend_checks: Dict[str, Gtk.CheckButton] = {}

        content = self.get_content_area()
        content.set_spacing(8)
        content.set_border_width(8)

        # --- General options ---

        self.notif_check = Gtk.CheckButton(label=notifications_label)
        self.notif_check.set_active(show_notifications)
        content.pack_start(self.notif_check, False, False, 0)

        self.held_check = Gtk.CheckButton(label=held_label)
        self.held_check.set_active(show_held_packages)
        content.pack_start(self.held_check, False, False, 0)

        # --- Backend section (only if any backends exist) ---

        if backend_states:
            sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            content.pack_start(sep, False, False, 6)

            backend_label = Gtk.Label(label=_("Backends"))
            backend_label.set_xalign(0)
            backend_label.get_style_context().add_class("heading")
            content.pack_start(backend_label, False, False, 0)

            for backend_id, label, enabled in backend_states:
                check = Gtk.CheckButton(label=label)
                check.set_active(enabled)
                content.pack_start(check, False, False, 0)
                self._backend_checks[backend_id] = check

        self.show_all()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_values(self) -> dict:
        """Return dialog values as a plain dict."""
        return {
            "show_notifications": self.notif_check.get_active(),
            "show_held_packages": self.held_check.get_active(),
            "backend_visibility": {
                backend_id: check.get_active()
                for backend_id, check in self._backend_checks.items()
            },
        }
