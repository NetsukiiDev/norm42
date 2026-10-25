# norm42

[![CI](https://github.com/NetsukiiDev/norm42/actions/workflows/ci.yml/badge.svg)](https://github.com/NetsukiiDev/norm42/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A small Bash wrapper for [42 Norminette](https://github.com/42School/norminette): clear the terminal, check your code, and keep the original output and exit status.

```bash
norm42
# Equivalent to:
clear
norminette -R CheckForbiddenSourceHeader .
```

## Features

- Always passes `-R CheckForbiddenSourceHeader` before your arguments.
- Checks the current directory when no arguments are supplied.
- Delegates C/header file discovery and recursion to Norminette itself.
- Accepts multiple files, directories, absolute paths and quoted paths with spaces.
- Does not filter diagnostics or modify your source files.
- Preserves Norminette's exit status using `exec`.
- Installs for one user without sudo or package-manager changes.

This is an independent helper, not an official 42 or Moulinette project. It does not reproduce Moulinette or guarantee evaluation results. The meaning of `-R` depends on the installed Norminette version; some releases describe it as a Norminette 2 compatibility option. This wrapper passes it unchanged, rather than implementing its own checks.

## Requirements and compatibility

| Component | Requirement |
| --- | --- |
| Runtime | Bash 3.2 or newer; `clear` (usually provided by ncurses) |
| Checker | A working `norminette` executable in `PATH` |
| Installation | Standard Unix tools: `mkdir`, `dirname`, `cmp`, `mktemp`, `cp`, `install`, `mv`, `rm` |
| Calling shell | Bash, Zsh, Fish or another shell that can run executables |
| Desktop | No desktop dependencies; Hyprland, GNOME and KDE settings are untouched |

### Operating systems

| Operating system | Support and verification |
| --- | --- |
| Linux — Arch, Ubuntu, Debian, Fedora and similar distributions | Supported when the requirements above are available. Locally verified on Arch Linux; automated tests passed on Ubuntu. Other distributions have not been individually tested. |
| macOS | Supported when the requirements above are available. Automated tests passed on the GitHub-hosted macOS runner. Intel and Apple Silicon are expected to work, but CI does not separately verify both architectures. |
| Windows with WSL | Expected to work inside a Linux distribution with the required dependencies; not directly tested on WSL. Install and run from the Linux shell. |
| Native Windows — PowerShell or Command Prompt | Not supported. Use WSL instead. Git Bash and other compatibility layers are not tested or supported. |
| FreeBSD, OpenBSD and other BSD systems | Potentially compatible with Bash and the required Unix tools installed; not tested or officially supported. |

The calling shell can be Bash, Zsh or Fish; the script itself always runs with Bash. No particular desktop environment or window manager is required. Installing the wrapper does not require sudo; its dependencies must be installed separately and available in `PATH`.

Locally verified with Norminette 3.3.54. CI tests the wrapper and installer using a mock checker; it does not certify every Norminette release, OS version or hardware architecture. See the [CI results](https://github.com/NetsukiiDev/norm42/actions/workflows/ci.yml) for the latest status. Norminette itself must also support your chosen platform.

## Install without sudo

```bash
git clone https://github.com/NetsukiiDev/norm42.git
cd norm42
./install.sh
```

The default destination is **`$HOME/.local/bin/norm42`**. The installer does not install dependencies, edit shell configuration, or request administrator permissions. If Norminette is absent it prints a warning; the installed command exits with status `127` until the dependency is available.

If needed, follow the upstream Norminette installation instructions. With `pipx` already available, a user installation is possible with `pipx install norminette`; make sure its executable directory is in your `PATH`.

Choose a different writable directory:

```bash
./install.sh --bin-dir "$HOME/tools/bin"
```

### Make the command available in new terminals

First check whether the directory is already on `PATH`. **Do not add duplicate entries.** For the default directory, add one of the following only if needed:

**Bash** (`~/.bashrc`) or **Zsh** (`~/.zshrc`):

```bash
case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) export PATH="$HOME/.local/bin:$PATH" ;;
esac
```

**Fish** (run once; persistent across sessions):

```fish
fish_add_path "$HOME/.local/bin"
```

Open a new terminal and check `command -v norm42`. For a custom installation directory, substitute that directory in the examples.

## Usage

```bash
norm42                              # Current directory, recursively
norm42 ft_putchar.c                 # One file
norm42 ex00/                        # One directory
norm42 ft_putchar.c ft_putstr.c      # Multiple files
norm42 include/example.h            # A header
norm42 "/home/user/42/C/c01"         # Absolute path
norm42 "directory with spaces/"     # Paths with spaces
```

Arguments are forwarded as `"$@"`, without glob expansion by the script. Shell globs such as `norm42 *.c` are expanded by your calling shell. Norminette's options, file selection, warnings and exit-code conventions remain its own. For example, a missing path may not cause a failure in every Norminette version.

`clear` runs before every invocation, including `norm42 --help`. A terminal with a valid `TERM` is needed for screen clearing. If `clear` fails, the checker still runs and its status is returned. How much scrollback is cleared depends on the terminal and its terminfo entry.

## Update and uninstall

An identical installation is a no-op. A different existing file is never replaced without `--force`:

```bash
git pull --ff-only
./install.sh --force
```

Before replacement, `--force` preserves the existing file beside the command as `norm42.backup.XXXXXX`. Symlinks and non-regular destinations are refused even with `--force`. Existing backups are never automatically deleted.

```bash
./uninstall.sh
# Or, for a custom destination:
./uninstall.sh --bin-dir "$HOME/tools/bin"
```

Uninstall only removes a file identical to `bin/norm42` in the current checkout. Modified files, symlinks, and different installed versions are left untouched. It does not remove Norminette, backups, directories or PATH settings. Use the matching checkout to uninstall an older version.

## Development

```bash
for script in bin/norm42 install.sh uninstall.sh; do bash -n "$script"; done
python3 -m unittest discover -s tests -v
```

Tests require Python 3.8+ and use isolated temporary directories, not your projects or real installation. They verify argument boundaries, the required rule, ordering, output, exit codes, installer collision protection, backups and safe uninstall. Norminette is not required for the automated unit tests.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE).
