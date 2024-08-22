#!/usr/bin/python3
# encoding=utf-8
# -*- coding: UTF-8 -*-

# ------------------------------------------------------------------------
# Copyright (c) 2024 Alexandre Bento Freire. All rights reserved.
# Licensed under the GPLv3 License.
# ------------------------------------------------------------------------

# cSpell:ignoreRegExp (hexpand|keyval|reorderable|renametoix|setproctitle)
import io
import os
import re
import argparse
import setproctitle
import stat
import sys
import time
import yaml

import gi
gi.require_version("Gtk", "3.0")  # noqa
from gi.repository import Gtk,  Gdk, GLib

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-console", action='store_true', default=False, help="Console mode")  # noqa
arg_parser.add_argument("-start-index", type=int, default=1, help="Start index used with there is a %%0n macro")  # noqa
arg_parser.add_argument("-reg-ex", action='store_true', default=False, help="Uses regular expressions on the find field")  # noqa
arg_parser.add_argument("-include-ext", action='store_true', default=False,
                        help="Renames including the file extension")
arg_parser.add_argument("-find", default="", help="Text to Find")
arg_parser.add_argument("-replace", default="", help="Text to Replace")
arg_parser.add_argument("-allow-revert", action='store_true', default=False,
                        help="Generates a revert file (console mode)")
arg_parser.add_argument("-test-mode", action='store_true', default=False,
                        help="Outputs only the new result, doesn't rename (console mode)")
arg_parser.add_argument("-revert-last", action='store_true', default=False,
                        help="Reverts last rename and exits")
arg_parser.add_argument("files", nargs="*", help="Source files")
args = arg_parser.parse_args()


# ------------------------------------------------------------------------
#                               ConsoleRename
# ------------------------------------------------------------------------

class ConsoleRename:
    def __init__(self, args):
        self.args = args
        self.cfg = {
            "version": 1.0,
            "revert-path": os.path.join(os.environ["HOME"], ".revert-renames"),
            "allow-revert": False,
            "send-notification": False,
            "macros": ["%0n", "%00n", "%000n", "%Y-%m-%d", "%Y-%m-%d-%H_%M_%S", "%Y-%m-%d %H_%M_%S", "%I"]
        }
        self.cfg_name = os.path.join(GLib.get_user_config_dir(), 'renametoix', 'renametoix.yaml')
        self.load_cfg()
        self.files = []
        self.renames = []
        self.rename_count = 0
        self.allow_renames = False
        self.files_list_store = []

    def load_cfg(self):
        if os.path.isfile(self.cfg_name):
            with io.open(self.cfg_name, "r", encoding="utf8") as input_file:
                self.cfg = yaml.safe_load(input_file)
            input_file.close()

    def apply_macros(self, text, start_index, filename):
        text = re.sub(r"%(\d*)n", lambda m: "%0*d" % (len(m.group(1)) + 1, start_index), text)
        stamp_parts = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(os.path.getmtime(filename))).split("_")
        for index, macro_name in enumerate("YmdHMS"):
            text = text.replace(f"%{macro_name}", stamp_parts[index])
        text = text.replace(f"%E", os.path.splitext(filename)[1])
        return text

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

        self.revert_file.write(f"printf \"'{new_basename}' → '{basename}'" +
                               f"\\n\"\nmv '{new_fullname}' '{fullname}'\n")

    def generate_new_names(self, start_index, is_reg_ex, include_ext, before, after):
        new_filenames = set()
        self.renames.clear()
        self.allow_renames = True
        for index, filename in enumerate(self.files):
            basename = os.path.basename(filename)
            dirname = os.path.dirname(filename)
            from_text, ext = os.path.splitext(basename) if not include_ext else (basename, None)
            new_text = re.sub(before, after, from_text, flags=re.A) if is_reg_ex \
                else from_text.replace(before, after)
            if new_text != from_text:
                if re.search(r"%[0A-Za-z]", new_text):
                    new_text = self.apply_macros(new_text, start_index, filename)
                    start_index += 1
                new_basename = (new_text + ext) if not include_ext else new_text
                new_filename = os.path.join(dirname, new_basename)
                self.files_list_store[index] = [dirname, basename, new_basename]
                if new_text:
                    self.renames.append([filename, new_filename])
                    self.allow_renames = self.allow_renames and new_filename not in new_filenames \
                        and not os.path.exists(new_filename)
                    if new_filename not in new_filenames:
                        new_filenames.add(new_filename)
                else:
                    self.allow_renames = False
            else:
                self.files_list_store[index] = [dirname, basename, basename]

    def add_files(self, filenames):
        for filename in filenames:
            if os.path.exists(filename) and filename not in self.files:
                basename = os.path.basename(filename)
                self.files_list_store.append([os.path.dirname(filename), basename, basename])
                self.files.append(filename)
        self.update_renames()

    def add_source_files(self):
        self.add_files([uri if not uri.startswith("file://") else
                        GLib.filename_from_uri(uri)[0] for uri in self.args.files])

    def update_renames(self):
        pass

    def console_apply_renames(self, allow_revert, test_mode=False):
        if self.allow_renames:
            try:
                for rename in self.renames:
                    src_file, dst_file = rename
                    if not os.path.exists(dst_file):
                        if not test_mode:
                            os.rename(src_file, dst_file)
                            if allow_revert:
                                self.add_revert(src_file, dst_file,
                                                os.path.basename(src_file), os.path.basename(dst_file))
                            self.rename_count += 1
                        else:
                            print(f"{src_file} -> {os.path.basename(dst_file)}")
            finally:
                self.close_revert_file()

    def close_revert_file(self):
        if self.rename_count and self.revert_file:
            self.revert_file.close()
            os.chmod(self.revert_name, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)
            main_revert_name = os.path.join(self.cfg["revert-path"], "revert-rename.sh")
            main_revert_file = open(main_revert_name, "w")
            main_revert_file.write(f"{self.revert_name}\n")
            main_revert_file.close()
            os.chmod(main_revert_name, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)

    def console_mode_rename(self):
        if args.revert_last:
            last_rename = os.path.join(self.cfg["revert-path"], "revert-rename.sh")
            if os.path.exists(last_rename):
                os.system(last_rename)
                os.unlink(last_rename)
                exit(1)
            else:
                sys.stderr.write(f"{last_rename} doesn't exists")
                exit(0)

        self.add_source_files()
        if not self.files:
            sys.stderr.write("No source files")
            exit(1)
        self.generate_new_names(self.args.start_index, self.args.reg_ex, self.args.include_ext,
                                self.args.find, self.args.replace)
        if not self.allow_renames:
            sys.stderr.write("Rename conflict")
            exit(1)
        self.console_apply_renames(self.args.allow_revert, self.args.test_mode)
        if self.rename_count:
            print(f"{self.rename_count} files renamed")

# ------------------------------------------------------------------------
#                               GUIRename
# ------------------------------------------------------------------------


class GUIRename(ConsoleRename):

    def __init__(self, args):
        super().__init__(args)
        self.ready = False
        self.sort_column = None
        self.current_folder = None

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(os.path.splitext(sys.argv[0])[0] + ".ui"))
        self.app_window = self.builder.get_object("app_window")
        self.find_entry = self.connect("find_entry",
                                       [[self.update_renames, "changed"], [self.entry_key_press, "key-press-event"]])
        self.replace_entry = self.connect("replace_entry",
                                          [[self.update_renames, "changed"], [self.entry_key_press, "key-press-event"]])
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
        self.connect("add_files_button", [[self.add_files_button_clicked]])
        self.connect("cancel_button", [[self.close_window]])
        self.ok_button = self.connect("ok_button", [[self.ok_button_clicked]])

        self.files_list_store = self.builder.get_object("files_list_store")
        self.files_treeview = self.builder.get_object("files_treeview")
        for i, column_title in enumerate(["Path", "Before", "After"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            column.set_resizable(True)
            column.set_reorderable(True)
            column.set_clickable(True)
            column.connect("clicked", self.files_column_clicked)
            self.files_treeview.append_column(column)

        self.settings_dialog = self.builder.get_object("settings_dialog")
        self.settings_dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.revert_dialog = self.builder.get_object("revert_dialog")
        self.revert_dialog.add_buttons(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
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

        self.add_source_files()
        screen = Gdk.Display.get_default().get_monitor(0).get_geometry()
        self.app_window.set_default_size(screen.width, screen.height - 100)
        self.app_window.connect("delete-event", Gtk.main_quit)
        self.app_window.show_all()
        self.ready = True
        self.update_renames()

    # Events

    def about_button_clicked(self, widget):
        self.about_dialog.run()
        self.about_dialog.hide()

    def add_files_button_clicked(self, width):
        dialog = Gtk.FileChooserDialog(
            title="Add Files", parent=self.app_window, action=Gtk.FileChooserAction.OPEN,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
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
            script_name, caption = self.revert_files_with_caption[path.get_indices()[0]]
            if script_name and self.confirmation_dialog("Are you sure want to execute %s?" % caption):
                os.system(os.path.join(self.cfg['revert-path'], os.path.join(script_name)))

    def files_column_clicked(self, column):
        if self.sort_column:
            self.sort_column.set_sort_indicator(False)
        column.set_sort_indicator(True)
        column.set_sort_order(Gtk.SortType.ASCENDING)
        self.sort_column = column

    def macro_button_clicked(self, widget):
        if self.find_entry.get_text() == "":
            self.reg_ex_button.set_active(True)
            self.find_entry.set_text("^.*$")
        self.replace_entry.set_text((self.replace_entry.get_text().strip() + f" {widget.get_label()}").strip())
        self.update_renames()

    def open_revert_folder_button_clicked(self, widget):
        os.system(f"xdg-open {self.cfg['revert-path']}")

    def ok_button_clicked(self, widget):
        self.apply_renames()
        self.close_window()

    def revert_dialog_clicked(self, widget):
        revert_list_store = self.builder.get_object("revert_list_store")
        if os.path.isdir(self.cfg["revert-path"]):
            self.revert_files_with_caption = []
            for script in sorted(os.listdir(self.cfg["revert-path"]), reverse=True):
                if script.endswith(".sh"):
                    caption = "Latest Revert" if script == "revert-rename.sh" else \
                        re.sub(r"revert-rename-([0-9-]+)-(\d+)_(\d+)_(\d+)\.sh", r"\1 \2:\3:\4", script)
                    self.revert_files_with_caption.append([script, caption])
                    revert_list_store.append([caption])

        self.revert_dialog.run()
        revert_list_store.clear()
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
                macros_editor_buffer.get_start_iter(), macros_editor_buffer.get_end_iter(), True).strip().split("\n")
            self.update_macro_widgets()
            self.save_cfg()
        self.settings_dialog.hide()

    # Methods

    def apply_renames(self):
        if self.allow_renames:
            self.console_apply_renames(self.cfg["allow-revert"])
            self.notify_msg(f"{self.rename_count} files renamed")

    def close_window(self, widget=None):
        Gtk.main_quit()

    def confirmation_dialog(self, message):
        dialog = Gtk.MessageDialog(message_format=message)
        dialog.add_button("_Yes", Gtk.ResponseType.YES)
        dialog.add_button("_No", Gtk.ResponseType.NO)
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
            os.system(f"command -v notify-send >/dev/null && notify-send -t 3000 '{msg}' > /dev/null 2>&1")

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

    def update_renames(self, widget=None):
        if self.ready:
            self.generate_new_names(
                self.start_index_label_spin.get_value_as_int(),
                self.reg_ex_button.get_active(),
                self.include_ext_button.get_active(),
                self.find_entry.get_text(),
                self.replace_entry.get_text()
            )
            self.ok_button.set_sensitive(self.allow_renames)

    def save_cfg(self):
        cfg_path = os.path.dirname(self.cfg_name)
        if not os.path.isdir(cfg_path):
            os.makedirs(cfg_path)
        with open(self.cfg_name, "wt", encoding="utf8") as output_file:
            output_file.write(yaml.dump(self.cfg, default_flow_style=False, sort_keys=False,
                                        allow_unicode=True, encoding="utf-8", width=200).decode("utf-8"))
            output_file.close()
            self.update_macro_widgets()


if not args.console and not args.revert_last:
    setproctitle.setproctitle("renametoix")
    win = GUIRename(args)
    Gtk.main()
else:
    ConsoleRename(args).console_mode_rename()
