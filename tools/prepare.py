#!/usr/bin/env python3
import os
import re
import argparse
from datetime import datetime
import shutil

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(file_path):
    with open(os.path.join(project_root, file_path), 'r') as file:
        return file.read()


def write_file(file_path, content):
    with open(os.path.join(project_root, file_path), 'w') as file:
        file.write(content)


def get_change_log_version():
    if not (match := re.search(r'^renametoix \(([0-9\.]+)\)', read_file('debian/changelog'))):
        print("No version on changelog.")
        return False
    return match.group(1)


# ------------------------------------------------------------------------
#                               update_changelog_date
# ------------------------------------------------------------------------

def update_changelog_date(folder):
    change_log_name = f'{folder}/changelog'
    content = read_file(change_log_name)

    if not (match := re.search(r'-- .+ <.+>  (.+)', content)):
        print("No date found in the changelog.")
        return False

    old_date = match.group(1)
    current_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    print(f"Old date: {old_date}, Current date: {current_date}")
    write_file(change_log_name, content.replace(old_date, current_date, 1))
    print("Changelog date updated")
    return True


# ------------------------------------------------------------------------
#                               update_ui_version
# ------------------------------------------------------------------------

def update_ui_version():
    version = get_change_log_version()
    if not version:
        return False
    print(f"Version: {version}")
    ui_filename = 'usr/lib/renametoix/renametoix.ui'
    content = re.sub(r'(<property name="version">)[0-9\.]+(</property>)',
                     lambda m: m.group(1) + version + m.group(2),
                     read_file(ui_filename))
    if f'<property name="version">{version}</property>' not in content:
        print("Version not found in the UI file.")
        return False
    write_file(ui_filename, content)
    print(f"{ui_filename} version updated")
    return True


# ------------------------------------------------------------------------
#                               prepare_pip
# ------------------------------------------------------------------------

CHANGELOG_FILE = 'debian-crenametoix/changelog'

def prepare_pip(update_version):
    if update_version:
        changelog_content = read_file(CHANGELOG_FILE)

        match = re.search(r'^(c?)renametoix \(([0-9\.]+)\)', changelog_content)
        if not match:
            print("No version on changelog.")
            return False

        if match.group(1) == "":
            fixed_content = re.sub(r'^renametoix', 'crenametoix', changelog_content, count=1)
            write_file(CHANGELOG_FILE, fixed_content)
            print(f"Fixed package name in {CHANGELOG_FILE}")

        version = match.group(2)
        print(f"Version: {version}")

        toml_filename = 'pyproject.toml'
        content = re.sub(r'(version = ")[0-9\.]+(")',
                         lambda m: m.group(1) + version + m.group(2),
                         read_file(toml_filename))
        write_file(toml_filename, content)
        print(f"{toml_filename} version updated")

    os.chdir(project_root)
    shutil.rmtree('src', ignore_errors=True)
    os.makedirs('src/crenametoix/plugins', exist_ok=True)
    write_file('src/crenametoix/__init__.py', '')
    shutil.copyfile('usr/lib/renametoix/crenametoix.py', 'src/crenametoix/crenametoix.py')
    for file in os.listdir('usr/lib/renametoix/plugins'):
        if file.endswith('.py'):
            shutil.copyfile(f'usr/lib/renametoix/plugins/{file}', f'src/crenametoix/plugins/{file}')
    print("Files Copied")
    return True


# ------------------------------------------------------------------------
#                               clean
# ------------------------------------------------------------------------

def clean():
    os.chdir(project_root)
    shutil.rmtree('dist', ignore_errors=True)
    shutil.rmtree('src', ignore_errors=True)
    # shutil.rmtree('.tox', ignore_errors=True)
    shutil.rmtree('tests/__pycache__', ignore_errors=True)


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-folder", type=str, default="debian")
arg_parser.add_argument("-no-update-version", action="store_true")
arg_parser.add_argument("action", choices=[
    "update-changelog-date",
    "update-ui-version",
    "prepare-pip",
    "clean"
])
args = arg_parser.parse_args()
action = args.action

if action == "update-changelog-date":
    exit(int(not update_changelog_date(args.folder)))
elif action == "update-ui-version":
    exit(int(not update_ui_version()))
elif action == "prepare-pip":
    exit(int(not prepare_pip(not args.no_update_version)))
elif action == "clean":
    clean()
