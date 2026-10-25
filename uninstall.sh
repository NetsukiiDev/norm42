#!/usr/bin/env bash
set -euo pipefail

program=norm42
root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
bin_dir=${HOME:?HOME must be set}/.local/bin

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
        --help|-h)
            printf 'Usage: %s [--bin-dir DIR]\nRemove only an unmodified installation of %s from this checkout.\n' "$0" "$program"
            exit 0
            ;;
        *) printf 'Error: unknown option: %s\n' "$1" >&2; exit 64 ;;
    esac
done

destination=$bin_dir/$program
if [[ ! -e $destination && ! -L $destination ]]; then
    printf 'Not installed: %s\n' "$destination"
    exit 0
fi
if [[ -L $destination || ! -f $destination ]] || ! cmp -s -- "$root/bin/$program" "$destination"; then
    printf 'Error: refusing to remove a symlink, modified file or different version: %s\n' "$destination" >&2
    exit 1
fi
rm -- "$destination"
printf 'Removed: %s\n' "$destination"
