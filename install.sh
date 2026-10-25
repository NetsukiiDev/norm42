#!/usr/bin/env bash
set -euo pipefail

program=norm42
root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
bin_dir=${HOME:?HOME must be set}/.local/bin
force=false

usage() {
    printf 'Usage: %s [--bin-dir DIR] [--force] [--help]\n' "$0"
    printf 'Install %s for the current user, without sudo.\n' "$program"
}

while (( $# )); do
    case "$1" in
        --bin-dir)
            if (( $# < 2 )) || [[ -z $2 ]]; then
                printf 'Error: --bin-dir requires a directory.\n' >&2
                exit 64
            fi
            bin_dir=$2
            shift 2
            ;;
        --force) force=true; shift ;;
        --help|-h) usage; exit 0 ;;
        *) printf 'Error: unknown option: %s\n' "$1" >&2; usage >&2; exit 64 ;;
    esac
done

mkdir -p -- "$bin_dir"
bin_dir=$(CDPATH= cd -- "$bin_dir" && pwd)
destination=$bin_dir/$program
source_file=$root/bin/$program

if [[ -L $destination || ( -e $destination && ! -f $destination ) ]]; then
    printf 'Error: refusing to replace a symlink or non-regular file: %s\n' "$destination" >&2
    exit 1
fi

if [[ -f $destination ]]; then
    if cmp -s -- "$source_file" "$destination" && [[ -x $destination ]]; then
        printf 'Already installed: %s\n' "$destination"
        exit 0
    fi
    if [[ $force != true ]]; then
        printf 'Error: %s already exists. Use --force to back it up and replace it.\n' "$destination" >&2
        exit 1
    fi
    backup=$(mktemp "$destination.backup.XXXXXX")
    cp -p -- "$destination" "$backup"
    printf 'Backup: %s\n' "$backup"
fi

temporary=$(mktemp "$bin_dir/.$program.install.XXXXXX")
trap 'rm -f -- "$temporary"' EXIT
install -m 755 -- "$source_file" "$temporary"
mv -f -- "$temporary" "$destination"
printf 'Installed: %s\n' "$destination"

if ! command -v norminette >/dev/null 2>&1; then
    printf 'Warning: install Norminette separately and make it available in PATH.\n' >&2
fi
if ! command -v clear >/dev/null 2>&1; then
    printf 'Warning: clear was not found in PATH.\n' >&2
fi
case ":${PATH-}:" in
    *":$bin_dir:"*) ;;
    *) printf 'Add this directory to your shell PATH: %s\nSee README.md for Bash, Zsh and Fish instructions.\n' "$bin_dir" ;;
esac
