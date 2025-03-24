#!/usr/bin/env bash

#set -x

. ./vendor/kisstdlib/devscript/test-cli-lib.sh

usage() {
    cat << EOF
# usage: $0 [--help] [--wine] [--output-version VERSION] PATH [PATH ...]

Sanity check and test \`hoardy-adb\` command-line interface.

## Example

\`\`\`
$0 backup.ab backup2.ab
\`\`\`
EOF
}

ORIG_PWD=$PWD
export PYTHONPATH="$PWD:$PYTHONPATH"

in_wine=
self() {
    if [[ -z "$in_wine" ]]; then
        python3 -m hoardy_adb "$@"
    else
        wine python -m hoardy_adb "$@"
    fi
}

fixed_stdio() {
    local src="$1"
    local target="$2"
    shift 2

    ok_stdio2 "$target.out" "$@"
    fixed_file "$src" "$target.out"
}

fixed_everything() {
    local src="$1"
    local target="$2"
    local res="$3"
    shift 3

    fixed_stdio "$src" "$target" "$@"
    cat "$res" | sha256sum - > "$target.res.sha256"
    fixed_file "$src" "$target.res.sha256"
}

[[ $# < 1 ]] && die "need at least one source"

opts=1
subset=
short=
oversion=5

while (($# > 0)); do
    if [[ -n "$opts" ]]; then
        case "$1" in
        --help) usage; exit 0; ;;
        --wine) in_wine=1 ; shift ; continue ;;
        --output-version) oversion=$2 ; shift 2 ; continue ;;
        --) opts= ; shift ; continue ;;
        esac
    fi

    src=$(readlink -f "$1")
    shift

    set_tmpdir

    cd "$tmpdir"

    echo "# Testing on $src in $tmpdir ..."

    cp -a "$src" original.ab
    [[ $? != 0 ]] && die "failed to copy"

    passfile="${src%.ab}.passphrase.txt"
    if [[ -e "$passfile" ]]; then
        cp "$passfile" original.passphrase.txt
    fi

    start "ls..."

    fixed_stdio "$src" ls \
                 self ls original.ab

    end

    start "ab2ab..."

    fixed_everything "$src" ab2ab original.stripped.ab \
                     self ab2ab original.ab

    fixed_everything "$src" ab2ab-c compressed.ab \
                     self ab2ab -c original.stripped.ab compressed.ab

    fixed_everything "$src" ab2ab-k stripped-k.ab \
                     self ab2ab -k original.ab stripped-k.ab

    fixed_stdio "$src" ab2ab-e \
                 self ab2ab -e --output-passphrase=secret stripped-k.ab encrypted.ab

    end

    start "split and merge..."

    fixed_stdio "$src" split \
                 self split original.ab

    fixed_stdio "$src" merge \
                 self merge hoardy_adb_split_* merged.ab

    equal_file original.stripped.ab merged.ab

    end

    start "unwrap and wrap..."

    fixed_everything "$src" ab2tar original.tar \
                     self ab2tar original.ab

    fixed_everything "$src" tar2ab wrapped.ab \
                     self tar2ab --output-version=$oversion original.tar wrapped.ab

    equal_file original.stripped.ab wrapped.ab

    end

    cd "$ORIG_PWD"
    rm -rf "$tmpdir"
done

finish
