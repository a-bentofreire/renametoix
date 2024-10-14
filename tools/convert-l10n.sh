#!/usr/bin/env bash
# --------------------------------------------------------------------
# Copyright (c) 2024 Alexandre Bento Freire. All rights reserved.
# Licensed under the GPL-2.0 license
# --------------------------------------------------------------------

# ------------------------------------------------------------------------
# Compile Translations
# ------------------------------------------------------------------------

SCRIPT_PATH="$(dirname $(realpath "$0"))"
python $SCRIPT_PATH/convert-l10n.py || exit 1
cd "$SCRIPT_PATH/../l10n"
find . -iname "*.po" -exec bash -c 'FILE="{}"; MSG_PATH=../usr/share/locale/"${FILE%.*}"/LC_MESSAGES; mkdir -p "$MSG_PATH"; echo Compile $FILE; msgfmt -o "$MSG_PATH/renametoix.mo" "$FILE";' \;
