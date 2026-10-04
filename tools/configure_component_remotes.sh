#!/bin/sh

set -eu

root=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$root" ] || [ "$PWD" != "$root" ]; then
    echo "error: run this script from the parent repository root" >&2
    exit 1
fi

check_initialized() {
    path=$1
    status_line=$(git submodule status -- "$path")
    case "$status_line" in
        -*|+*|U*)
            echo "error: submodule is not cleanly initialized: $path" >&2
            exit 1
            ;;
    esac
    if ! git -C "$path" rev-parse --verify HEAD >/dev/null 2>&1; then
        echo "error: submodule is not initialized: $path" >&2
        exit 1
    fi
}

ensure_remote() {
    path=$1
    remote=$2
    expected=$3
    if git -C "$path" remote get-url "$remote" >/dev/null 2>&1; then
        actual=$(git -C "$path" remote get-url "$remote")
        if [ "$actual" != "$expected" ]; then
            echo "error: $path remote $remote is $actual, expected $expected" >&2
            exit 1
        fi
    else
        git -C "$path" remote add "$remote" "$expected"
    fi
}

check_initialized components/fdkernel
check_initialized components/freecom
check_initialized components/country

ensure_remote components/fdkernel origin https://github.com/nakatamaho/fdkernel.git
# From M20 the official FreeDOS repositories are upstream; lpproj is the
# NEC PC-98/DBCS reference remote. Through M19 upstream meant lpproj.
ensure_remote components/fdkernel upstream https://github.com/FDOS/kernel.git
ensure_remote components/fdkernel lpproj https://github.com/lpproj/fdkernel.git
ensure_remote components/freecom origin https://github.com/nakatamaho/freecom_dbcs2.git
ensure_remote components/freecom upstream https://github.com/FDOS/freecom.git
ensure_remote components/freecom lpproj https://github.com/lpproj/freecom_dbcs2.git
ensure_remote components/country origin https://github.com/FDOS/country.git

echo "component remotes verified"
