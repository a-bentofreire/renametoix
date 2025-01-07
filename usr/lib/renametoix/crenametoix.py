#!/usr/bin/python3
# encoding=utf-8
# -*- coding: UTF-8 -*-

# ------------------------------------------------------------------------
# Copyright (c) 2024-2025 Alexandre Bento Freire. All rights reserved.
# Licensed under the GPLv3 License.
# ------------------------------------------------------------------------

# cSpell:ignoreRegExp (hexpand|keyval|reorderable|renametoix|setproctitle|thunar|nemo|renamer)
import os
import re
import argparse
import sys
import time
import threading
import importlib

sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), 'plugins'))

STATE_ALREADY_EXISTS = -4
STATE_EMPTY = -3
STATE_NOT_CHANGED = -2
STATE_RENAMED = -1


def _(text): return text


macros_functions = {
    "upper": lambda m: m.upper(),
    "u": lambda m: m.upper(),
    "lower": lambda m: m.lower(),
    "l": lambda m: m.lower(),
    "capitalize": lambda m: m.capitalize(),
    "c": lambda m: m.capitalize(),
    "title": lambda m: m.title(),
    "t": lambda m: m.title()
}

console_mode_text = _("Console Mode")


def add_arguments(arg_parser):
    arg_parser.add_argument("-start-index", type=int, default=1,
                            help=_("Start index used with there is a %0n macro").replace("%", "%%")
                            )  # noqa
    arg_parser.add_argument("-reg-ex", action='store_true', default=False,
                            help=_("Uses regular expressions on the find field"))  # noqa
    arg_parser.add_argument("-include-ext", action='store_true', default=False,
                            help=_("Renames including the file extension"))
    arg_parser.add_argument("-find", default="", help=_("Text to Find"))
    arg_parser.add_argument("-replace", default="", help=_("Text to Replace"))
    arg_parser.add_argument("-test-mode", action='store_true', default=False,
                            help="%s (%s)" % (_("Outputs only the new result, doesn't rename"),
                                              console_mode_text))


# ------------------------------------------------------------------------
#                               Plugin
# ------------------------------------------------------------------------

class Plugin:
    def __init__(self, plugin_name):
        self.is_slow = False
        try:
            self.worker = importlib.import_module(plugin_name).get_worker()
            self.extensions = self.worker.get_extensions()
        except:
            self.worker = None

    def set_new_files(self, new_files):
        if self.worker:
            self.new_files = self.filter_by_extension(new_files)
            if self.new_files:
                self.is_slow = self.is_slow or self.worker.is_slow()

    def filter_by_extension(self, files):
        return list(
            filter(lambda f: os.path.splitext(f)[1].lower()
                   in self.extensions, files)) if self.extensions and self.worker else files


# ------------------------------------------------------------------------
#                               G_File
# ------------------------------------------------------------------------

class G_File():
    def __init__(self, filename):
        self.filename = filename

    def get_basename(self):
        return os.path.basename(self.filename)

    def get_path(self):
        return self.filename

    def has_parent(self):
        return os.path.dirname(self.filename) != self.filename

    def get_parent(self):
        return G_File(os.path.dirname(self.filename))

    def query_exists(self):
        return os.path.exists(self.filename)

    def is_native(self):
        return True


# ------------------------------------------------------------------------
#                               G_FileBridge
# ------------------------------------------------------------------------

class G_FileBridge:
    def get_g_file(self, filename):
        return G_File(filename)

    def get_g_file_from_uri(self, uri):
        at = uri.find("://")
        return self.get_g_file(uri[at + 3:]) if at >= 0 else self.get_g_file(uri)

    def rename_file(self, g_source, g_dest, is_native):
        os.rename(g_source.get_path(), g_dest.get_path())


# ------------------------------------------------------------------------
#                               ConRename
# ------------------------------------------------------------------------

class PureConsoleRename(G_FileBridge):

    def __init__(self, args):
        self.args = args
        self.files = []
        self.files_list_store = []
        self.files_state = []
        self.renames = []
        self.rename_count = 0
        self.allow_renames = False
        self.plugins = {}
        self.prepared_files_count = 0
        self.thread_running = False
        self.demon = None
        self.exception = None

    def macro_functions(self, group_nr, macro_name, groups):
        if len(groups) <= group_nr:
            return ""
        text = groups[group_nr]
        func = macros_functions.get(macro_name)
        return func(text) if func else text

    def run_python_expr(self, script, groups):
        try:
            return eval(f"lambda m: {script}")(groups)
        except:
            return groups(0)

    def apply_macros(self, text, start_index, filename, groups):
        text = re.sub(r"%(\d*)n", lambda m: "%0*d" % (len(m.group(1)) + 1, start_index), text)
        text = re.sub(r"%(\d)\{([a-z]+)\}", lambda m: self.macro_functions(
            int(m.group(1)), m.group(2), groups), text)
        text = re.sub(r"%:\{([^}]+)\}", lambda m: self.run_python_expr(m.group(1), groups), text)
        text = re.sub(r"%!\{(\w+):([^}]+)\}", lambda m:
                      self.run_plugin_expr(m.group(1), m.group(2), filename, groups), text)
        stamp_parts = time.strftime("%Y_%m_%d_%H_%M_%S",
                                    time.localtime(os.path.getmtime(filename))).split("_")
        for index, macro_name in enumerate("YmdHMS"):
            text = text.replace(f"%{macro_name}", stamp_parts[index])
        basename, ext = os.path.splitext(os.path.basename(filename))
        text = text.replace(f"%B", basename).replace(f"%E", ext)
        return text

    def set_file_index_new_name(self, index, new_name=None):
        self.files_list_store[index][2] = new_name if new_name is not None \
            else self.files_list_store[index][1]

    def generate_new_names(self, start_index, is_reg_ex, include_ext, find, replace):
        new_filenames = {}
        self.renames.clear()
        for index, filename in enumerate(self.files):
            self.set_file_index_new_name(index)
            self.files_state[index] = STATE_NOT_CHANGED
        self.allow_renames = find != "" or replace != ""
        if not self.allow_renames:
            return

        try:
            for index, filename in enumerate(self.files):
                g_file = self.get_g_file(filename)
                basename = g_file.get_basename()
                dirname = g_file.get_parent().get_path() if g_file.has_parent() else ""
                from_text, ext = os.path.splitext(basename) \
                    if not include_ext else (basename, None)
                find_text = find or (from_text if not is_reg_ex else "^(.*)$")
                new_text = re.sub(find_text, replace, from_text, flags=re.A) if is_reg_ex \
                    else from_text.replace(find_text, replace)

                if new_text and re.search(r"%[0-9A-Za-z:!]", new_text):
                    groups = [find_text]
                    if is_reg_ex:
                        matches = re.search(find_text, from_text, flags=re.A)
                        if matches:
                            groups = [matches.group(0)] + list(matches.groups())
                    try:
                        new_text = self.apply_macros(new_text, start_index, filename, groups)
                    except Exception as e:
                        self.set_file_index_new_name(index)
                        self.files_state[index] = str(e.args[0]) if len(e.args) > 0 else ""
                        continue
                    start_index += 1

                new_basename = (new_text + ext) if not include_ext else new_text
                new_filename = os.path.join(dirname, new_basename)
                self.set_file_index_new_name(index, new_basename)
                if basename != new_basename:
                    if new_basename:
                        if not self.get_g_file(new_filename).query_exists():
                            conflict_index = new_filenames.get(new_filename)
                            if conflict_index is None:
                                new_filenames[new_filename] = index
                                self.renames.append([filename, new_filename])
                                self.files_state[index] = STATE_RENAMED
                            else:
                                self.files_state[index] = conflict_index
                        else:
                            self.files_state[index] = STATE_ALREADY_EXISTS
                    else:
                        self.files_state[index] = STATE_EMPTY

            self.allow_renames = len(self.renames) > 0
        except Exception as e:
            self.exception = e
            self.allow_renames = False

    def get_state_description(self, state):
        return state if type(state) == str else {
            STATE_ALREADY_EXISTS: _("Already exists"),
            STATE_EMPTY: _("Empty"),
            STATE_NOT_CHANGED: _("Not changed"),
            STATE_RENAMED: _("Renamed")
        }.get(state, _("Conflicts with file") + (": %s" % self.files_list_store[state][1]))

    def add_files(self, uris):
        for uri in uris:
            g_file = self.get_g_file_from_uri(uri)
            filename = g_file.get_path()
            if g_file.query_exists() and filename not in self.files:
                basename = g_file.get_basename()
                self.files_list_store.append(
                    [g_file.get_parent().get_path() if g_file.has_parent() else "",
                     basename, basename])
                self.files.append(filename)
                self.files_state.append(STATE_NOT_CHANGED)
        self.update_renames()

    def add_source_files(self):
        self.add_files(self.args.files)

    def update_renames(self):
        # to override
        pass

    def after_rename(self, src_file, dst_file, is_native):
        # to override
        pass

    def wait_until(self, callback):
        self.demon.join()
        callback()

    def console_apply_renames(self, test_mode=False, is_silent=False):
        if self.allow_renames:
            for rename in self.renames:
                src_file, dst_file = rename
                g_source = self.get_g_file(src_file)
                g_dest = self.get_g_file(dst_file)
                is_native = g_source.is_native()
                if not g_dest.query_exists():
                    if not test_mode:
                        self.rename_file(g_source, g_dest, is_native)
                        self.after_rename(src_file, dst_file, is_native)
                        self.rename_count += 1
                    if not is_silent:
                        print(f"{src_file} -> {self.get_g_file(dst_file).get_basename()}")

    def display_descriptions(self):
        for index, filename in enumerate(self.files):
            state = self.files_state[index]
            if state != STATE_RENAMED:
                sys.stdout.write(f"{filename}: {self.get_state_description(state)}\n")

    def console_mode_rename_ready(self, is_sync):
        self.generate_new_names(self.args.start_index, self.args.reg_ex, self.args.include_ext,
                                self.args.find, self.args.replace)
        if not self.allow_renames:
            if self.exception:
                sys.stderr.write(_("Error") + f" {self.exception}\n")
            else:
                self.display_descriptions()
            exit(1)
        self.console_apply_renames(self.args.test_mode)
        if self.rename_count:
            sys.stdout.write((_('%d files renamed') % self.rename_count) + "\n")
        self.display_descriptions()

    def console_mode_rename(self):
        self.add_source_files()
        if not self.files:
            sys.stderr.write(_("No files") + "\n")
            exit(1)
        self.init_plugins(self.args.replace, self.console_mode_rename_ready, True)

    # Plugins

    def prepare_plugins(self, callback, is_sync):
        for plugin in self.plugins.values():
            if plugin.worker:
                plugin.worker.prepare(plugin.new_files)
        if is_sync:
            callback(is_sync)
        else:
            self.wait_until(callback)

    def run_plugin_expr(self, plugin_name, macro, filename, groups):
        plugin = self.plugins.get(plugin_name)
        return plugin.worker.eval_expr(macro, filename, groups) \
            if plugin and plugin.worker else macro

    def init_plugins(self, replace_field, callback, is_console):
        plugin_names = set(re.findall(r"%!\{(\w+):[^}]*\}", replace_field))
        if not plugin_names or (set(self.plugins.keys()) == set(plugin_names) and
                                len(self.files) == self.prepared_files_count):
            return callback(True)

        is_async = False
        new_files = self.files[self.prepared_files_count:]
        for plugin_name in plugin_names:
            plugin = self.plugins.get(plugin_name)
            if not plugin:
                plugin = Plugin(plugin_name)
                plugin.set_new_files(self.files)
                self.plugins[plugin_name] = plugin
            else:
                plugin.set_new_files(new_files)
            is_async = is_async or plugin.is_slow

        self.prepared_files_count = len(self.files)

        if not is_async or is_console:
            self.prepare_plugins(callback, True)
        else:
            self.thread_running = True
            self.demon = threading.Thread(target=self.prepare_plugins,
                                          args=(callback, False), daemon=True)
            self.demon.start()

def run_as_package():
    arg_parser = argparse.ArgumentParser()
    add_arguments(arg_parser)
    arg_parser.add_argument("files", nargs="*", help=_("Files"))
    args = arg_parser.parse_args()
    PureConsoleRename(args).console_mode_rename()

if __name__ == "__main__":
    run_as_package()