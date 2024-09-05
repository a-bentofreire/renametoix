#!/usr/bin/env bash
cd "$(dirname "$0")"
VER=$(sed -E -n '1s/renametoix \(([0-9\.]+).*/\1/p' ../debian/changelog)
[[ -z $VER ]] && printf "Missing version\n" >&2 && exit 1
printf "Update UI file to $VER\n"
sed -E -i "s#(<property name=\"version\">)[0-9\.]+(</property>)#\1$VER\2#" ../usr/lib/renametoix/renametoix.ui
