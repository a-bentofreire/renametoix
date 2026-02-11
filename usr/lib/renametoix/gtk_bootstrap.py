# ruff: noqa: E402

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Gio", "2.0")

from gi.repository import Gtk, Gdk, Gio, GLib

__all__ = ["Gtk", "Gdk", "Gio", "GLib"]
