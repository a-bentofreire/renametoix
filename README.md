# Description

[RenameToIX](https://www.devtoix.com/en/projects/renametoix) is a visual Linux Gtk file renamer featuring an advanced macro ecosystem, seamlessly integrating with Nemo, Nautilus, and Thunar file managers.

For `crenametoix`, the console version without Gtk dependencies, read [here](https://www.devtoix.com/en/projects/renametoix#crenametoix)

Simple macro example:

![Image](https://cdn.jsdelivr.net/gh/a-bentofreire/a-bentofreire/media/renametoix/RenameToIX-Index-Macro-1.gif)

Python lambda expression example:

![Image](https://cdn.jsdelivr.net/gh/a-bentofreire/a-bentofreire/media/renametoix/RenameToIX-Python-Expressions-1.gif)

Reverse Geocoding macro example:

![Image](https://cdn.jsdelivr.net/gh/a-bentofreire/a-bentofreire/media/renametoix/RenameToIX-Reverse-Geocoding-1.gif)

Doc Header macro example:

![Image](https://cdn.jsdelivr.net/gh/a-bentofreire/a-bentofreire/media/renametoix/RenameToIX-Doc-Header-1.gif)

Read section [Integrate](#integrate) on now to integrate with Nemo, Nautilus and Thunar.

If you find this project useful, please, read the [Support this Project](#support-this-project) on how to contribute.  

## Features

- GUI and Console mode. (¹)
- **Single click macro**.
- Counter, file datetime, and extension Macros.
- Function Macros with regex group capture: `lower`, `upper`, `capitalize` and `title`.
- Python lambda expressions macro.
- Reverse geocoding of JPEG images from GPS information macro via [geo plugin](#geo-plugin).
- Header of Word documents macro via [doc plugin](#doc-plugin).
- Custom macro extensions using [plugins](#plugins).
- Start index for counter macro.
- Configurable list of macros.

- Revert previous renames (first activate on Settings dialog). (¹)
- Send notification after renames (first activate on Settings dialog). (¹)
- Integration with Nemo, Nautilus and Thunar File Manager. (¹)
- Limited support for [mtp devices](#mtp-devices) (Smartphones, Cameras, etc...). (¹)
- Translated into multiple languages *1*

(¹) - supported only on renametoix but not on [crenametoix](#crenametoix)

## Installation

```bash
sudo add-apt-repository ppa:a-bentofreire/toix
sudo apt-get update
sudo apt install renametoix
```

## crenametoix

**crenametoix** is a version of renametoix for console only without Gtk dependencies,
it supports all the features including plugins, except: translations, mtp devices, revert and notifications.  
Configuration files aren't generated.

```bash
sudo add-apt-repository ppa:a-bentofreire/toix
sudo apt-get update
sudo apt install crenametoix
```

**crenametoix** can also be installed via pip

```bash
pip install crenametoix
```

## Requirements

RenameToIX uses `xdg-open` and `notify-send` external commands.

## Macros

- `%n, %0n ... %00000n` - counter
- `%B` - file basename (without extension)
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
- `%!{geo:%country%, %city%}` - replaces with the "country", "city" from the JPEG image GPS info via [geo plugin](#geo-plugin)
- `%!{doc:%header%}` - replaces with the "header" with the first header in a doc file [doc plugin](#doc-plugin)

## Macro functions

The macro functions can also be used with regular expressions to capture groups.

ex1:
- Replace: `%0{title}`
- Filename: `my document.png` will become `My Document.png`

ex2:
- Find: `..(NEW).(design)`
- Replace: `%1{l}-%2{u}`
- Filename: `n-myNEW design.png` will become `n-new-DESIGN.png`

ex3:
- Find: ``
- Replace: `new-%B ready`
- Filename: `design.png` will become `new-design ready.png`

## Python Lambda Expressions

The `%:{expr}` will internally evaluate a lambda expression: `eval(f"lambda m: {expr}")(groups)`

where groups are:
- if regular expressions, then are the captured groups from a regular expression.
- otherwise, it's the text to find.

ex:
- Find: `^(.*)-(.*)$`
- Replace: `%:{m[2] - m[1]}`
- Regular Expression: `checked`.
- Filename: `code-actions.py` will become `Actions - Code.py`

### Features and Limitations

- The expression can't contain a closed curly bracket `}`.
- The evaluator doesn't do any security checks, so run it at your own risk.

## Plugins

The `%!{plugin_name:expr}` will call an external plugin to evaluate the expression.  

- Plugins are python scripts located on `/usr/lib/renametoix/plugins`.
- A plugin must have a function named `get_worker()`, returning an instance of a class with the following methods:
- The expression can't contain a closed curly bracket `}`.

| Method | Description |
| -- | -- |
| `is_slow(self)` | returns `True` if the plugin requires slow operations |
| `get_extensions(self)` | returns a list of file extensions supported |
| `eval_expr(self, macro, filename, groups)` | evaluates a macro. It should be a fast operation |
| `prepare(self, files)` | for each file, it will prepare the macro evaluation<br>if `is_slow` is `True`, it will run in a working thread if it's GUI mode |

## Geo Plugin

Geo Plugin performs reverse geocoding.

- Requires install python packages: `pip install geopy piexif`.
- Supports the following geocoding fields: `country`, `state`, `city`, `postcode`, `suburb`.
- Supports `.jpg` and `.jpeg` file extensions.
- Ending spaces, commas and semi-commas are striped.

ex:
- Replace: `%!{geo:%country%, %city%}`
- Filename: `IMG_.jpg` will become `MyCountry, MyCity.jpg`

## Doc Plugin

Doc Plugin extracts the first header from a Word doc/docx file.

- Requires install python package: `pip install python-docx`.
- Supports the following geocoding fields: `header`.
- Supports `.doc` and `.docx` file extensions.

ex:
- Replace: `%!{doc:%header%}`
- Filename: `a.docx` will become `MyHeaderH1.docx`

## Running in console mode

To activate on console mode, use `--console` on command line:

```plaintext
usage: renametoix [-h] [-console] [-start-index START_INDEX] [-reg-ex] [-include-ext] [-find FIND] [-replace REPLACE] [-allow-revert] [-test-mode] [-revert-last] [files ...]

positional arguments:
  files                 Source files

options:
  -h, --help            show this help message and exit
  -console              Console mode (¹)
  -start-index START_INDEX
                        Start index used with there is a %0n macro
  -reg-ex               Uses regular expressions on the find field
  -include-ext          Renames including the file extension
  -find FIND            Text to Find
  -replace REPLACE      Text to Replace
  -allow-revert         Generates a revert file (console mode) (¹)
  -test-mode            Outputs only the new result, doesn't rename (console mode) (¹)
  -revert-last          Reverts last rename and exits (¹)
```

(¹) - supported only on renametoix but not on [crenametoix](#crenametoix)

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
- Russian
- Ukrainian

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

## Contributions

- [claimsecond](https://github.com/claimsecond) - Translations in Russian and Ukrainian

## Copyrights

(c) 2024-2025 [Alexandre Bento Freire](https://www.a-bentofreire.com)
