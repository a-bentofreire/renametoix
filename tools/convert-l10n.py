#!/usr/bin/env python3
import sys
import csv
import re
import os
import json

langs = ['pt']


def main():
    script_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    base_path = os.path.abspath(os.path.join(script_path, '..'))
    l10n_file = os.path.join(base_path, 'l10n/l10n.csv')

    desktop_file = os.path.join(base_path, 'usr/share/applications/renametoix.desktop')
    messages_path = os.path.join(base_path, 'l10n')

    with open(l10n_file, 'r', encoding='utf-8') as map_f:
        reader = csv.DictReader(map_f, delimiter='\t')
        headers = reader.fieldnames

        for lang in langs:
            translations = {}

            for row in reader:
                key = row[headers[0]]
                translation = row[lang].rstrip()
                translation = translation if translation != '' else row['en']
                translations[key] = translation

            def po_replace(match):
                msgid = match.group(1)
                return f'msgid "{msgid}"\nmsgstr "{translations[msgid]}"' \
                    if msgid in translations else match.group(0)

            messages_file = os.path.join(messages_path, f"{lang}.po")
            with open(messages_file, 'r+', encoding='utf-8') as f:
                lines = f.read()
                f.seek(0)
                lines = re.sub(r'msgid\s+"([^"]+)"\s*\nmsgstr\s+"[^"]+"', po_replace, lines, flags=re.DOTALL)
                f.write(lines)
                f.truncate()
                f.close()
            print(f'File saved as: {messages_file}')

            with open(desktop_file, 'r+', encoding='utf-8') as f:
                lines = f.read()
                f.seek(0)
                matches = re.search(r"\nDescription=(.*)\n", lines)
                desc = translations[matches.group(1)]
                lines = re.sub(fr'Description\[{lang}\]=.*\n', "", lines)
                lines += f'Description[{lang}]={desc}\n'
                f.write(lines)
                f.truncate()
                f.close()
            print(f'File saved as: {desktop_file}')


if __name__ == '__main__':
    main()
