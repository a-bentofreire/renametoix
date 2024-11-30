#!/usr/bin/env python3
import sys
import csv
import re
import os
import shutil
import argparse

locales = ['pt', 'es', 'de', 'ru', 'uk']


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-update-locales", action='store')
    args = arg_parser.parse_args()
    update_mode = args.update_locales is not None
    update_locales = (args.update_locales or "").split(",")
    script_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    base_path = os.path.abspath(os.path.join(script_path, '..'))
    l10n_file = os.path.join(base_path, 'l10n/l10n.csv')

    desktop_file = os.path.join(base_path, 'usr/share/applications/renametoix.desktop')
    messages_path = os.path.join(base_path, 'l10n')

    rows_by_key = {}
    key_names = []
    with open(l10n_file, 'r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file, delimiter='\t')
        headers = reader.fieldnames

        for index, locale in enumerate(locales):
            translations = {}

            for row in reader:
                key = row[headers[0]]
                translation = row[locale].rstrip()
                translation = translation if translation != '' else row['en']
                translations[key] = translation
                if index == 0:
                    key_names.append(key)
                rows_by_key[key] = (rows_by_key.get(key) or {'en': key}) | {locale: row[locale]}
            csv_file.seek(0)

            if update_mode and locale not in update_locales:
                continue

            def po_replace(match):
                msgid = match.group(1)
                return f'msgid "{msgid}"\nmsgstr "{translations[msgid]}"' \
                    if msgid in translations else match.group(0)

            messages_file = os.path.join(messages_path, f"{locale}.po")
            if not os.path.exists(messages_file):
                shutil.copy(os.path.join(messages_path, "en.po"), messages_file)
            with open(messages_file, 'r+' if not update_mode else 'r', encoding='utf-8') as f:
                lines = f.read()
                if not update_mode:
                    f.seek(0)
                    lines = re.sub(r'msgid\s+"([^"]+)"\s*\nmsgstr\s+"[^"]+"',
                                   po_replace, lines, flags=re.DOTALL)
                    f.write(lines)
                    f.truncate()
                    print(f'File saved as: {messages_file}')
                else:
                    matches = re.findall(r'msgid\s+"(.+)"\s*\nmsgstr\s+"(.*)"', lines)
                    for key, translation in matches:
                        if rows_by_key.get(key):
                            if translation != rows_by_key[key][locale]:
                                rows_by_key[key][locale] = translation
                                print(f"Update {locale}| {key}={translation}")
                        else:
                            sys.stderr.write(f"ERROR: Locale {locale} uses invalid key '{key}'\n")

            with open(desktop_file,  'r+' if not update_mode else 'r', encoding='utf-8') as f:
                lines = f.read()
                if not update_mode:
                    f.seek(0)
                    matches = re.search(r"\nDescription=(.*)\s*\n", lines)
                    desc = translations.get(matches.group(1))
                    if desc:
                        lines = re.sub(fr'Description\[{locale}\]=.*\n', "", lines)
                        lines += f'Description[{locale}]={desc}\n'
                    else:
                        sys.stderr.write(f"ERROR: Missing translation for '{
                                         matches.group(1)}' used on {desktop_file}\n")
                    if not update_mode:
                        f.write(lines)
                        f.truncate()
                        f.close()
                        print(f'File saved as: {desktop_file}')
                else:
                    key = re.search(r"Description=(.*)", lines).group(1)
                    translation = re.search(fr"Description\[{locale}\]=(.*)", lines).group(1)
                    if translation != rows_by_key[key][locale]:
                        rows_by_key[key][locale] = translation
                        print(f"Update {locale}| {key}={translation}")

    if update_mode:
        csv_name, csv_ext = os.path.splitext(l10n_file)
        l10n_file_updated = f"{csv_name}-updated{csv_ext}"
        with open(l10n_file_updated, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers, delimiter='\t')
            writer.writeheader()
            for key in key_names:
                writer.writerow(rows_by_key[key])
        print(f"Save {l10n_file_updated}")


if __name__ == '__main__':
    main()
