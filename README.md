# Description

[Renametoix](https://www.devpieces.com/projects/renametoix) is a Gtk3 file renamer designed to be an alternative to [Linux Mint](https://www.linuxmint.com/) bulky as bulk file renamer on nemo File Manager.

![Image](https://www.devpieces.com/files/projects/renametoix/example-macro.gif)

## Features

- Counter, file datetime, and extension Macros.
- Start index for counter Macro.
- Configurable list of macros.
- Single click macro.
- Revert previous renames (first activate on Settings dialog).
- Send notification after renames (first activate on Settings dialog).

## Installation

```bash
sudo add-apt-repository ppa:a-bentofreire/toix
sudo apt-get update
sudo apt install renametoix
```

## Requirements

Renametoix uses `xdg-open` and `notify-send` external commands.

## Macros

- `%n, %0n ... %00000n` - counter
- `%E` - file extension
- `%Y` - file 4-digit year
- `%m` - file 2-digit month
- `%d` - file 2-digit day
- `%H` - file 2-digit hour
- `%M` - file 2-digit minute
- `%S` - file 2-digit second

## Configure nemo

To use `renametoix` as a file renamer instead of `bulky` on nemo tweak the following setting:

Menu Edit -> Preferences -> Behavior -> Bulk Rename

## License

GPLv3 License

## Copyrights

(c) 2024 [Alexandre Bento Freire](https://www.a-bentofreire.com)
