# i3-autoswitch

Auto-switch to a window's workspace on i3 window open/move events.

When a new window appears (or is moved) on another workspace, this script switches your view to that workspace automatically.

## Requirements

- Python 3.10+
- Python package: `i3ipc`

## Installation

1. Clone this repository.
2. Install dependency:

```sh
python3 -m pip install -r requirements.txt
```

## Usage

```sh
$ python src/main.py -h
usage: main.py [-h] [--debug]

Auto-switch to a window's workspace on i3 window open/move events.

options:
  -h, --help  show this help message and exit
  --debug     Enable debug logs to stderr.
```

## Auto-start with i3

Add this line to your i3 config (usually `~/.config/i3/config`):

```text
exec_always --no-startup-id python3 /absolute/path/to/i3-autoswitch/src/main.py
```

Then reload i3 config:

```sh
i3-msg restart
```
