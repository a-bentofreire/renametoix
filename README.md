# Description

[RenameToIX](https://www.devtoix.com/en/projects/renametoix) is a Gtk3 File Renamer designed to be an alternative to [Linux Mint](https://www.linuxmint.com/) bulky as file renamer on Nemo and Thunar File Manager.

![Image](https://www.devtoix.com/files/projects/renametoix/example-macro.gif)

## Features

- GUI and Console mode.
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

RenameToIX uses `xdg-open` and `notify-send` external commands.

## Macros

- `%n, %0n ... %00000n` - counter
- `%E` - file extension
- `%Y` - file 4-digit year
- `%m` - file 2-digit month
- `%d` - file 2-digit day
- `%H` - file 2-digit hour
- `%M` - file 2-digit minute
- `%S` - file 2-digit second

## Running in console mode

To activate on console mode, use `--console` on command line:

```
usage: renametoix [-h] [-console] [-start-index START_INDEX] [-reg-ex] [-include-ext] [-find FIND] [-replace REPLACE] [-allow-revert] [-test-mode] [-revert-last] [files ...]

positional arguments:
  files                 Source files

options:
  -h, --help            show this help message and exit
  -console              Console mode
  -start-index START_INDEX
                        Start index used with there is a %0n macro
  -reg-ex               Uses regular expressions on the find field
  -include-ext          Renames including the file extension
  -find FIND            Text to Find
  -replace REPLACE      Text to Replace
  -allow-revert         Generates a revert file (console mode)
  -test-mode            Outputs only the new result, doesn't rename (console mode)
  -revert-last          Reverts last rename and exits
```

## Revert the last rename in console mode

If the previous console mode rename was executed with `-allow-revert`, then:  
`renametoix -revert-last` will revert the last rename.

## Configure Nemo

To use `renametoix` as a file renamer instead of `bulky` on nemo tweak the following setting:

Menu Edit -> Preferences -> Behavior -> Bulk Rename

## Configure Thunar

Menu Edit -> Configure Custom Actions -> "+" sign -> Edit Action  
Name: RenameToIX  
Command: /usr/bin/renametoix %F  

RenameToIX will appear on the context menu.

## License

GPLv3 License

## Copyrights

(c) 2024 [Alexandre Bento Freire](https://www.a-bentofreire.com)
