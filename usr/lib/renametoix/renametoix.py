#!/usr/bin/python3
# encoding=utf-8
# -*- coding: UTF-8 -*-

# ------------------------------------------------------------------------
# Copyright (c) 2024-2025 Alexandre Bento Freire. All rights reserved.
# Licensed under the GPLv3 License.
# ------------------------------------------------------------------------

# cSpell:ignoreRegExp (hexpand|keyval|reorderable|renametoix|setproctitle|thunar|nemo|renamer)
import io
import os
import re
import argparse
import setproctitle
import stat
import sys
import time
import yaml
import gettext
import locale
import crenametoix

import gi
gi.require_version("Gtk", "3.0")  # noqa
gi.require_version('Gio', '2.0')  # noqa
from gi.repository import Gtk, Gdk, GLib, Gio

APP = 'renametoix'
LOCALE_DIR = "/usr/share/locale"
locale.bindtextdomain(APP, LOCALE_DIR)
gettext.bindtextdomain(APP, LOCALE_DIR)
gettext.textdomain(APP)
_ = gettext.gettext

REVERT_RENAME_SH = "revert-rename.sh"

console_mode_text = _("Console Mode")
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-console", action='store_true', default=False,
                        help=console_mode_text)  # noqa
crenametoix.add_arguments(arg_parser)
arg_parser.add_argument("-allow-revert", action='store_true', default=False,
                        help="%s (%s)" % (_("Generates a revert script"), console_mode_text))
arg_parser.add_argument("-revert-last", action='store_true', default=False,
                        help=_("Reverts last rename and exits"))
arg_parser.add_argument("files", nargs="*", help=_("Files"))
args = arg_parser.parse_args()

# ------------------------------------------------------------------------
#                               ConsoleRename
# ------------------------------------------------------------------------


class ConsoleRename(crenametoix.PureConsoleRename):
    def __init__(self, args):
        super().__init__(args)
        self.cfg = {
            "version": 1.0,
            "revert-path": os.path.join(os.environ["HOME"], ".revert-renames"),
            "allow-revert": False,
            "send-notification": False,
            "macros": [
                "%0n", "%00n", "%000n", "%Y-%m-%d", "%Y-%m-%d-%H_%M_%S", "%Y-%m-%d %H_%M_%S",
                "%0{upper}", "%0{lower}", "%0{capitalize}",
                "%1{upper}", "%1{lower}", "%1{capitalize}",
                "%:{m[0]}",
                "%!{geo:%country%, %city%}",
                "%!{doc:%header%}",
                "%B", "%E",
            ]
        }
        self.default_macros = self.cfg["macros"]
        self.cfg_name = os.path.join(GLib.get_user_config_dir(), 'renametoix', 'renametoix.yaml')
        self.revert_file = None
        self.load_cfg()

    def get_g_file(self, filename):
        return Gio.File.new_for_path(filename)

    def get_g_file_from_uri(self, uri):
        return Gio.File.new_for_uri(uri) if "://" in uri else Gio.File.new_for_path(uri)

    def wait_until(self, callback):
        GLib.idle_add(callback, False)
        pass

    def rename_file(self, g_source, g_dest, is_native):
        if is_native:
            g_source.move(g_dest, Gio.FileCopyFlags.NONE, None, None, None, None)
        else:
            try:
                src_stream = g_source.read(None)
                dest_stream = g_dest.replace(None, False, Gio.FileCreateFlags.NONE, None)
                buffer_size = 8192
                while True:
                    data = src_stream.read_bytes(buffer_size, None)
                    if data.get_size() == 0:
                        break
                    dest_stream.write_bytes(data, None)
                src_stream.close(None)
                dest_stream.close(None)
                g_source.delete(None)
            except GLib.Error as e:
                print(f"Error during rename operation: {e}")

    def load_cfg(self):
        if os.path.isfile(self.cfg_name):
            with io.open(self.cfg_name, "r", encoding="utf8") as input_file:
                self.cfg = yaml.safe_load(input_file)
            input_file.close()

    # Revert Files

    def add_revert(self, fullname, new_fullname, basename, new_basename):
        fullname = os.path.abspath(fullname)
        new_fullname = os.path.abspath(new_fullname)
        if self.rename_count == 0:
            if not os.path.exists(self.cfg["revert-path"]):
                os.makedirs(self.cfg["revert-path"], 0o700)
            self.revert_name = os.path.join(self.cfg["revert-path"], "revert-rename-") + \
                time.strftime("%Y-%m-%d-%H_%M_%S.sh", time.localtime())
            self.revert_file = open(self.revert_name, "w")
            self.revert_file.write("echo Reverting Changes:\n\n")

        self.revert_file.write(f"printf \"'{new_basename}' → '{basename}'\\n\" 2>/dev/null\n"
                               f"mv '{new_fullname}' '{fullname}'\n")

    def exec_revert_script(self, revert_basename=None):
        revert_script = self.get_revert_script(revert_basename)
        if not revert_basename and not os.path.exists(revert_script):
            self.populate_revert_list_store([])
            if len(self.revert_scripts_with_caption) == 0:
                return 1
            revert_script = self.get_revert_script(self.revert_scripts_with_caption[0][0])

        if os.path.exists(revert_script):
            if revert_script == self.get_revert_script():
                with open(revert_script, "r") as f:
                    target_script = f.read().strip()
                    f.close()
                os.unlink(revert_script)
                revert_script = target_script
            print(f"Execute {revert_script}")
            os.system(revert_script)
            os.unlink(revert_script)
            return 0
        else:
            sys.stderr.write("%s doesn't exists" % revert_script)
            return 1

    def close_revert_script(self):
        if self.rename_count and self.revert_file:
            self.revert_file.close()
            os.chmod(self.revert_name, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)
            main_revert_name = self.get_revert_script()
            main_revert_file = open(main_revert_name, "w")
            main_revert_file.write(f"{self.revert_name}\n")
            main_revert_file.close()
            os.chmod(main_revert_name, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)

    def get_revert_script(self, revert_basename=None):
        return os.path.join(self.cfg["revert-path"], revert_basename or REVERT_RENAME_SH)

    def populate_revert_list_store(self, revert_list_store):
        revert_list_store.clear()
        if os.path.isdir(self.cfg["revert-path"]):
            self.revert_scripts_with_caption = []
            for script in sorted(os.listdir(self.cfg["revert-path"]), reverse=True):
                if script.endswith(".sh"):
                    caption = _("Latest Revert") if script == REVERT_RENAME_SH else \
                        re.sub(r"revert-rename-([0-9-]+)-(\d+)_(\d+)_(\d+)\.sh",
                               r"\1 \2:\3:\4", script)
                    self.revert_scripts_with_caption.append([script, caption])
                    revert_list_store.append([caption])
        return revert_list_store

    def console_apply_renames(self, test_mode=False, allow_revert=None, is_silent=False):
        if self.allow_renames:
            try:
                self.allow_revert = allow_revert if allow_revert is not None \
                    else self.args.allow_revert
                super().console_apply_renames(test_mode, is_silent)
            finally:
                self.close_revert_script()

    def console_mode_rename(self):
        if args.revert_last:
            exit(self.exec_revert_script())
        super().console_mode_rename()

    def after_rename(self, src_file, dst_file, is_native):
        if self.allow_revert and is_native:
            self.add_revert(src_file, dst_file, os.path.basename(src_file),
                            os.path.basename(dst_file))

    # Integrations

    def get_integrations_paths(self):
        home = os.environ["HOME"]
        return {
            "thunar": os.path.join(home, ".config/Thunar/uca.xml"),
            "nautilus": os.path.join(home, ".local/share/nautilus/scripts/RenameToIX"),
            "nemo": os.path.join(home, ".local/share/nemo/actions/RenameToIX.nemo_action")
        }

    def get_allowed_integrations(self):
        paths = self.get_integrations_paths()
        return {
            "thunar": os.path.exists("/usr/bin/thunar") and os.path.exists(paths["thunar"]),
            "nautilus": os.path.exists("/usr/bin/nautilus"),
            "nemo-renamer": os.path.exists("/usr/bin/nemo"),
            "nemo": os.path.exists("/usr/bin/nemo")
        }

    def set_integrations(self, to_integrate):
        paths = self.get_integrations_paths()
        if "nemo-renamer" in to_integrate:
            try:
                Gio.Settings.new("org.nemo.preferences"). \
                    set_value("bulk-rename-tool",
                              GLib.Variant("ay", "/usr/bin/renametoix".encode('utf-8') + b'\0'))
            except:
                pass

        if "nemo" in to_integrate and not os.path.exists(paths["nemo"]):
            os.makedirs(os.path.dirname(paths["nemo"]), exist_ok=True)
            with open(paths["nemo"], "w") as f:
                f.write("""[Nemo Action]
Active=true
Exec=bash -c "/usr/bin/renametoix %F"
Selection=notnone
Extensions=any
Name=RenameToIX
Quote=single""")
                f.close()

        if "nautilus" in to_integrate and not os.path.exists(paths["nautilus"]):
            os.makedirs(os.path.dirname(paths["nautilus"]), exist_ok=True)
            with open(paths["nautilus"], "w") as f:
                f.write("/usr/bin/renametoix $NAUTILUS_SCRIPT_SELECTED_URIS "
                        ">/tmp/nautilus-script.log 2>>/tmp/nautilus-script-err.log")
            os.chmod(paths["nautilus"], stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)

        if "thunar" in to_integrate:
            with open(paths["thunar"], "r+") as f:
                content = f.read()
                if "renametoix" not in content:
                    content = content.replace("</actions>", """<action>
\t<icon>/usr/share/icons/hicolor/scalable/apps/renametoix.svg</icon>
\t<name>RenameToIX</name>
\t<submenu></submenu>
\t<unique-id>1724283846660573-2</unique-id>
\t<command>/usr/bin/renametoix %F</command>
\t<description></description>
\t<range>*</range>
\t<patterns>*</patterns>
\t<directories/>
\t<audio-files/>
\t<image-files/>
\t<other-files/>
\t<text-files/>
\t<video-files/>
</action>
</actions>""")
                    f.seek(0)
                    f.write(content)
                    f.truncate()


# ------------------------------------------------------------------------
#                               GUIRename
# ------------------------------------------------------------------------

class GUIRename(ConsoleRename):

    def __init__(self, args):
        super().__init__(args)
        self.ready = False
        self.append_new_default_macros()
        self.sort_column = None
        self.current_folder = None

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(APP)
        self.builder.add_from_file(os.path.join(os.path.splitext(sys.argv[0])[0] + ".ui"))
        self.app_window = self.builder.get_object("app_window")
        self.find_entry = self.connect("find_entry",
                                       [[self.update_renames, "changed"],
                                        [self.entry_key_press, "key-press-event"]])
        self.replace_entry = self.connect("replace_entry",
                                          [[self.update_renames, "changed"],
                                           [self.entry_key_press, "key-press-event"]])
        self.start_index_label_spin = self.connect("start_index_label_spin",
                                                   [[self.update_renames, "change-value"]])
        self.start_index_label_spin.set_adjustment(Gtk.Adjustment(
            value=1, lower=0, upper=100, step_increment=1, page_increment=10))
        self.start_index_label_spin.connect("value-changed", self.update_renames)
        self.reg_ex_button = self.connect("reg_ex_button", [[self.update_renames]])
        self.include_ext_button = self.connect("include_ext_button", [[self.update_renames]])
        self.connect("macro_button", [[self.macro_button_clicked]])
        self.update_macro_widgets()
        self.connect("about_button", [[self.about_button_clicked]])
        self.connect("settings_button", [[self.settings_button_clicked]])
        self.connect("revert_button", [[self.revert_dialog_clicked]])
        self.add_files_button = self.connect("add_files_button", [[self.add_files_button_clicked]])
        self.cancel_button = self.connect("cancel_button", [[self.close_window]])
        # @TODO: Determine why isn't ui translating this button
        self.cancel_button.set_label(_("Cancel"))
        self.ok_button = self.connect("ok_button", [[self.ok_button_clicked]])

        self.files_list_store = self.builder.get_object("files_list_store")
        self.files_treeview = self.builder.get_object("files_treeview")
        self.files_treeview.connect("query-tooltip", self.on_query_tooltip)
        self.files_treeview.set_has_tooltip(True)

        def get_style_color(flag):
            rgba = style_context.get_color(flag)
            return f"rgba({int(rgba.red * 255)}, {int(rgba.green * 255)}, " + \
                f" {int(rgba.blue * 255)}, {rgba.alpha})"

        style_context = self.files_treeview.get_style_context()
        self.row_colors = {
            crenametoix.STATE_ALREADY_EXISTS: "rgba(220, 0, 0, 1)",
            crenametoix.STATE_EMPTY: get_style_color(Gtk.StateFlags.NORMAL),
            crenametoix.STATE_NOT_CHANGED: get_style_color(Gtk.StateFlags.INSENSITIVE),
            crenametoix.STATE_RENAMED: get_style_color(Gtk.StateFlags.SELECTED),
            0: "rgba(255, 0, 0, 1)"
        }

        for i, column_title in enumerate([_("Path"), _("Before"), _("After")]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            column.set_cell_data_func(renderer, self.set_row_color, None)
            column.set_resizable(True)
            column.set_reorderable(True)
            column.set_clickable(True)
            column.connect("clicked", self.files_column_clicked)
            self.files_treeview.append_column(column)

        self.settings_dialog = self.builder.get_object("settings_dialog")
        self.settings_dialog.add_buttons(_("Cancel"), Gtk.ResponseType.CANCEL,
                                         Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.connect("integrate_button", [[self.integrate_clicked]])

        self.integrate_dialog = self.builder.get_object("integrate_dialog")
        self.integrate_dialog.add_buttons(_("Cancel"), Gtk.ResponseType.CANCEL,
                                          Gtk.STOCK_OK, Gtk.ResponseType.OK)

        self.revert_dialog = self.builder.get_object("revert_dialog")
        self.revert_dialog.add_buttons(_("Close"), Gtk.ResponseType.CLOSE)
        self.revert_files_tree = self.builder.get_object("revert_files_tree")
        self.revert_files_tree.append_column(Gtk.TreeViewColumn("", Gtk.CellRendererText(), text=0))
        self.connect("execute_revert_button", [[self.execute_revert_button_clicked]])
        self.connect("open_revert_folder_button", [[self.open_revert_folder_button_clicked]])
        self.about_dialog = self.builder.get_object("about_dialog")

        self.start_index_label_spin.set_value(self.args.start_index)
        self.reg_ex_button.set_active(self.args.reg_ex)
        self.include_ext_button.set_active(self.args.include_ext)
        self.find_entry.set_text(self.args.find)
        self.replace_entry.set_text(self.args.replace)
        self.add_accelerators()
        self.add_source_files()
        screen = Gdk.Display.get_default().get_monitor(0).get_geometry()
        self.app_window.set_default_size(screen.width, screen.height - 100)
        self.app_window.connect("delete-event", Gtk.main_quit)
        self.app_window.show_all()
        self.ready = True
        self.update_renames()

    def on_query_tooltip(self, widget, x, y, _, tooltip):
        path, _, cx, cy = widget.get_path_at_pos(x, y) or (None, None, None, None)
        if path is not None:
            row_index = path.get_indices()[0] - 1
            if row_index >= 0:
                state = self.files_state[row_index]
                if state != crenametoix.STATE_RENAMED and state is not None:
                    tooltip.set_text(self.get_state_description(state))
                    return True
        return False

    def add_accelerators(self):
        accelerators = set()
        for object_name in [
            "find_label", "replace_label", "start_index_label",
                "reg_ex_button", "include_ext_button", "ok_button", "cancel_button"
        ]:
            obj = self.builder.get_object(object_name)
            caption = obj.get_text() if isinstance(obj, Gtk.Label) else obj.get_label()
            index = 0
            while caption[index].lower() in accelerators:
                index += 1
            caption = caption[0:index] + "_" + caption[index:]
            accelerators.add(caption[index + 1].lower())
            if isinstance(obj, Gtk.Label):
                obj.set_text(caption)
                obj.set_mnemonic_widget(obj.get_accel_widget())
            else:
                obj.set_label(caption)
            obj.set_use_underline(True)

    def append_new_default_macros(self):
        last_macro = self.default_macros[-1]
        if self.cfg.get("last-macro") != last_macro:
            self.cfg["last-macro"] = last_macro
            for macro in self.default_macros:
                if macro not in self.cfg["macros"]:
                    self.cfg["macros"].append(macro)
            self.save_cfg()

    # Events

    def set_row_color(self, column, cell, model, tree_iter, user_data):
        path = model[tree_iter].path
        if path is not None:
            row_index = path.get_indices()[0]
            state = self.files_state[row_index]
            color = self.row_colors.get(state) or self.row_colors[0]
            cell.set_property("foreground", color)

    def about_button_clicked(self, widget):
        self.about_dialog.run()
        self.about_dialog.hide()

    def add_files_button_clicked(self, width):
        dialog = Gtk.FileChooserDialog(
            title=_("Add Files"), parent=self.app_window, action=Gtk.FileChooserAction.OPEN,
            buttons=(_("Cancel"), Gtk.ResponseType.CANCEL, _("Open"), Gtk.ResponseType.OK))
        if self.current_folder:
            dialog.set_current_folder(self.current_folder)
        dialog.set_select_multiple(True)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.current_folder = dialog.get_current_folder()
            self.add_files(dialog.get_filenames())
        dialog.destroy()

    def entry_key_press(self, widget, event):
        if event.keyval == 0xFF1B:
            self.close_window()
        elif event.keyval == 0xFF0D:
            self.apply_renames()
            self.close_window()

    def execute_revert_button_clicked(self, widget):
        path, _focus = self.revert_files_tree.get_cursor()
        if path:
            script_name, caption = self.revert_scripts_with_caption[path.get_indices()[0]]
            if script_name and self.confirmation_dialog(
                    _("Are you sure want to execute %s?") % caption):
                self.exec_revert_script(script_name)
                self.populate_revert_list_store(self.builder.get_object("revert_list_store"))

    def files_column_clicked(self, column):
        if self.sort_column:
            self.sort_column.set_sort_indicator(False)
        column.set_sort_indicator(True)
        column.set_sort_order(Gtk.SortType.ASCENDING)
        self.sort_column = column

    def macro_button_clicked(self, widget):
        self.replace_entry.set_text((self.replace_entry.get_text().strip()
                                     + f" {widget.get_label()}").strip())
        self.update_renames()

    def open_revert_folder_button_clicked(self, widget):
        os.system(f"xdg-open {self.cfg['revert-path']}")

    def ok_button_clicked(self, widget):
        self.apply_renames()
        self.close_window()

    def revert_dialog_clicked(self, widget):
        self.populate_revert_list_store(self.builder.get_object("revert_list_store"))
        self.revert_dialog.run()
        self.revert_dialog.hide()

    def settings_button_clicked(self, widget):
        revert_check = self.builder.get_object("revert_check")
        revert_check.set_active(self.cfg["allow-revert"])
        send_notification_check = self.builder.get_object("send_notification_check")
        send_notification_check.set_active(self.cfg["send-notification"])
        revert_path = self.builder.get_object("revert_path_entry")
        revert_path.set_text(self.cfg["revert-path"])
        macros_editor_buffer = self.builder.get_object("macros_editor_buffer")
        macros_editor_buffer.set_text("\n".join(self.cfg["macros"]))

        response = self.settings_dialog.run()
        if response == Gtk.ResponseType.OK:
            self.cfg["allow-revert"] = revert_check.get_active()
            self.cfg["send-notification"] = send_notification_check.get_active()
            self.cfg["revert-path"] = revert_path.get_text().strip()
            self.cfg["macros"] = macros_editor_buffer.get_text(
                macros_editor_buffer.get_start_iter(),
                macros_editor_buffer.get_end_iter(), True).strip().split("\n")
            self.update_macro_widgets()
            self.save_cfg()
        self.settings_dialog.hide()

    def integrate_clicked(self, widget):
        integrations = self.get_allowed_integrations()
        managers_names = {
            "nemo-renamer": "nemo_integrate_rename_check",
            "nemo": "nemo_action_check",
            "nautilus": "nautilus_script_check",
            "thunar": "thunar_action_check"
        }
        for name in managers_names.keys():
            check = self.builder.get_object(managers_names[name])
            if integrations[name]:
                check.set_active(True)
            else:
                check.set_sensitive(False)

        response = self.integrate_dialog.run()
        if response == Gtk.ResponseType.OK:
            to_integrate = []
            for name in managers_names.keys():
                if self.builder.get_object(managers_names[name]).get_active():
                    to_integrate.append(name)
            self.set_integrations(to_integrate)
        self.integrate_dialog.hide()

    # Methods

    def apply_renames(self):
        if self.allow_renames:
            self.console_apply_renames(allow_revert=self.cfg["allow-revert"], is_silent=True)
            self.notify_msg(_("%d files renamed") % self.rename_count)

    def close_window(self, widget=None):
        Gtk.main_quit()

    def confirmation_dialog(self, message):
        dialog = Gtk.MessageDialog(message_format=message)
        dialog.add_button("_" + _("Yes"), Gtk.ResponseType.YES)
        dialog.add_button("_" + _("No"), Gtk.ResponseType.NO)
        return_value = dialog.run()
        dialog.destroy()
        return return_value == Gtk.ResponseType.YES

    def connect(self, object_name, events):
        object = self.builder.get_object(object_name)
        for event in events:
            object.connect(event[1] if len(event) == 2 else "clicked", event[0])
        return object

    def notify_msg(self, msg=""):
        if self.cfg["send-notification"]:
            os.system("command -v notify-send >/dev/null && notify-send -t 3000 "
                      f"'{msg}' > /dev/null 2>&1")

    def update_macro_widgets(self):
        macros = self.cfg["macros"]
        macro_button = self.builder.get_object("macro_button")
        macro_button.set_label(macros[0] if len(macros) else "")
        macros_popup = self.builder.get_object("macros_popup")
        for child in macros_popup.get_children():
            macros_popup.remove(child)
            child.destroy()
        tooltip = macro_button.get_tooltip_text()
        for macro in macros:
            menuitem = Gtk.MenuItem(label=macro, visible=True)
            menuitem.set_tooltip_text(tooltip)
            menuitem.connect("activate", self.macro_button_clicked)
            macros_popup.append(menuitem)

    def visual_allow_renames(self, enabled):
        self.ok_button.set_sensitive(enabled)
        self.files_treeview.queue_draw()
        self.files_treeview.set_sensitive(enabled)
        self.add_files_button.set_sensitive(not self.thread_running)

    def update_rename_ready(self, is_sync):
        self.ready = True
        self.thread_running = False
        self.generate_new_names(
            self.start_index_label_spin.get_value_as_int(),
            self.reg_ex_button.get_active(),
            self.include_ext_button.get_active(),
            self.find_entry.get_text(),
            self.replace_entry.get_text()
        )
        self.visual_allow_renames(self.allow_renames)

    def update_renames(self, widget=None):
        if self.ready:
            self.ready = False
            self.visual_allow_renames(False)
            self.init_plugins(self.replace_entry.get_text(), self.update_rename_ready, False)

    def save_cfg(self):
        cfg_path = os.path.dirname(self.cfg_name)
        if not os.path.isdir(cfg_path):
            os.makedirs(cfg_path)
        with open(self.cfg_name, "wt", encoding="utf8") as output_file:
            output_file.write(yaml.dump(self.cfg, default_flow_style=False, sort_keys=False,
                                        allow_unicode=True, encoding="utf-8",
                                        width=200).decode("utf-8"))
            output_file.close()
        if self.ready:
            self.update_macro_widgets()


if not args.console and not args.revert_last:
    setproctitle.setproctitle("renametoix")
    win = GUIRename(args)
    Gtk.main()
else:
    ConsoleRename(args).console_mode_rename()
