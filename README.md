# Description

[RenameToIX](https://www.devtoix.com/en/projects/renametoix) is a visual Linux file renamer built with Gtk, designed to be an alternative to [Linux Mint](https://www.linuxmint.com/) bulky as file renamer for Nemo, Nautilus and Thunar File Managers.

Simple macro example:

![Image](https://cdn.jsdelivr.net/gh/a-bentofreire/a-bentofreire/media/renametoix/RenameToIX-Example-Macro.gif)

Python lambda expression example:

![Image](https://cdn.jsdelivr.net/gh/a-bentofreire/a-bentofreire/media/renametoix/RenameToIX-Python-Expressions.gif)

Read section [Integrate](#integrate) on now to integrate with Nemo, Nautilus and Thunar.

If you find this project useful, please, read the [Support this Project](#support-this-project) on how to contribute.  

## Features

- GUI and Console mode.
- **Single click macro**.
- Counter, file datetime, and extension Macros.
- Function Macros with regex group capture: `lower`, `upper`, `capitalize` and `title`.
- Evaluates Python lambda expressions a macro.
- Start index for counter Macro.
- Configurable list of macros.
- Revert previous renames (first activate on Settings dialog).
- Send notification after renames (first activate on Settings dialog).
- Integration with Nemo, Nautilus and Thunar File Manager.
- Limited support for [mtp devices](#mtp-devices) (Smartphones, Cameras, etc...).

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
- `%0{upper}` `%0{u}` - uppercase  (function)
- `%0{lower}` `%0{l}` - lowercase (function)
- `%0{capitalize}` `%0{c}` - capitalize (function)
- `%0{title}` `%0{t}` - capitalize (function)
- `%:{expr}` - evaluates [python lambda expressions](#python-lambda-expressions)

## Macro functions

The macro functions can also be used with regular expressions to capture groups.

ex:
- Find: `.^.*$`
- Replace: `%0{title}`
- Filename: `my document.png` will become `My Document.png`

- Find: `..(NEW).(design)`
- Replace: `%1{l}-%2{u}`
- Filename: `n-myNEW design.png` will become `n-new-DESIGN.png`

## Python Lambda Expressions

The `%:{expr}` will internally evaluate a lambda expression: `eval(f"lambda m: {expr}")(groups)`

where groups are the captured groups from a regular expression.

ex:
- Find: `.^(.*)-(.*)$`
- Replace: `%:{m[2] - m[1]}`
- Filename: `code-actions.py` will become `Actions - Code.py`

### Features and Limitations

- First, enable Regular Expression mode to capture groups.
- The script can't contain a closed curly bracket `}`.
- The evaluator doesn't do any security checks, so run it at your own risk.

## Running in console mode

To activate on console mode, use `--console` on command line:

```plaintext
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

## Integrate

RenameToIX can be integrated with Nemo, Nautilus and Thunar.
On RenameToIX application, click on the Settings button, and then `Integrate` button.

- Nemo Bulk Rename: When you press F2 it will use **RenameToIX** instead of bulky.
- Nemo Action: On context menu, it will include an item named **RenameToIX**.
- Nautilus Script: On context menu Scripts, it will include an item named **RenameToIX**.
- Thunar Action: On context menu, it will include an item named **RenameToIX**.

## Languages

- English
- Portuguese
- Spanish
- German

## Mtp Devices

RenameToIX can rename files on mtp devices with the following limitations:
- It doesn't support revert.
- The file is copied and the deleted the original, this is a slow operation and doesn't preserves the timestamp.
- When modifying the Find Replace fields, it's checking if the new filename exists on the destination. This is a slow operation.

## Translations

To improve translations:
- Clone the project from [Github](https://github.com/a-bentofreire).
- Update the translation on `tools/l10n.po`.
- Run `convert-l10n.sh`.

## Support this Project

If you find this project useful, consider supporting it:

- Donate:  

[![Donate via PayPal](https://www.paypalobjects.com/webstatic/en_US/i/btn/png/blue-rect-paypal-34px.png)](https://www.paypal.com/donate/?business=MCZDHYSK6TCKJ&no_recurring=0&item_name=Support+Open+Source&currency_code=EUR)

[![Buy me a Coffee](https://www.devtoix.com/assets/buymeacoffee-small.png)](https://buymeacoffee.com/abentofreire)

- Visit the project [homepage](https://www.devtoix.com/en/projects/renametoix)
- Give the project a ⭐ on [Github](https://github.com/a-bentofreire/renametoix)
- [Translate into your language](#translations)
- Spread the word
- Follow me:
  - [Github](https://github.com/a-bentofreire)
  - [LinkedIn](https://www.linkedin.com/in/abentofreire)
  - [Twitter/X](https://x.com/devtoix)

## License

GPLv3 License

## Copyrights

(c) 2024 [Alexandre Bento Freire](https://www.a-bentofreire.com)
