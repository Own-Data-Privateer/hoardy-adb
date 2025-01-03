#!/usr/bin/env bash

#set -x

usage() {
    cat << EOF
# usage: $0 [--help] [--output-version VERSION] PATH [PATH ...]

Sanity check and test \`hoardy-adb\` command-line interface.

## Example

\`\`\`
$0 backup.ab backup2.ab
\`\`\`
EOF
}

errors=0
task_errors=0
error() {
    echo -e "\e[1;31m" >&2
    echo -n "$*" >&2
    echo -e "\e[0m" >&2
    ((errors+=1))
    ((task_errors+=1))
}

die() {
    error "$*"
    exit 1
}

equal_file() {
    if ! diff -U 0 "$2" "$3"; then
        error "$1: equal_file failed"
    fi
}

fixed_target() {
    local target="$1"
    local expected="$2.$target"
    local got="$3/$target"

    if ! [[ -e "$expected" ]]; then
        cp "$got" "$expected"
        echo " created $expected"
    elif ! diff -U 0 "$expected" "$got"; then
        cp "$got" "$expected.new"
        error "$target: fixed_target failed"
    else
        rm -f "$expected.new"
    fi
}

raw() {
    python3 -m hoardy_adb "$@"
}

ok_raw() {
    raw "$@"
    code=$?
    if ((code != 0)); then
        die "$*: return code $code"
    fi
}

ok_separate() {
    local target="$1"
    local dst="$2"
    shift 2

    raw "$@" > "$dst/$target.stdout" 2> "$dst/$target.stderr"
    code=$?
    if ((code != 0)); then
        cat "$dst/$target.stderr" >&2
        die "$target: $*: return code $code"
    fi
}

ok_mixed() {
    local target="$1"
    local dst="$2"
    shift 2

    raw "$@" &> "$dst/$target.out"
    code=$?
    if ((code != 0)); then
        cat "$dst/$target.out" >&2
        die "$target: $*: return code $code"
    fi
}

no_stderr() {
    local target="$1"
    local dst="$2"
    shift 2

    ok_separate "$target" "$dst" "$@"
    if [[ -s "$dst/$target.stderr" ]]; then
        cat "$dst/$target.stderr" >&2
        error "$target: $*: stderr is not empty"
    fi
}

fixed_output() {
    local target="$1"
    local src="$2"
    local dst="$3"
    shift 3

    ok_mixed "$target" "$dst" "$@"
    fixed_target "$target.out" "$src" "$dst"
}

fixed_everything() {
    local target="$1"
    local src="$2"
    local dst="$3"
    local res="$4"
    shift 4

    fixed_output "$target" "$src" "$dst" "$@"
    cat "$dst/$res" | sha256sum - > "$dst/$target.res.sha256"
    fixed_target "$target.res.sha256" "$src" "$dst"
}

[[ $# < 1 ]] && die "need at least one source"
umask 077
trap '[[ -n "$td" ]] && rm -rf "$td"' 0

opts=1
subset=
short=
oversion=5

while (($# > 0)); do
    if [[ -n "$opts" ]]; then
        case "$1" in
        --help) usage; exit 0; ;;
        --output-version) oversion=$2 ; shift 2 ; continue ;;
        --) opts= ; shift ; continue ;;
        esac
    fi

    src=$1
    shift

    td=$(mktemp --tmpdir -d hoardy-adb-test-cli-XXXXXXXX)
    td=$(readlink -f "$td")

    task_started=

    start() {
        echo -n "## $1"
        task_started=$(date +%s)
        task_errors=0
    }

    end() {
        local now=$(date +%s)
        echo " $task_errors errors, $((now-task_started)) seconds"
    }

    echo "# Testing on $src in $td ..."

    cp -a "$src" "$td/original.ab"
    [[ $? != 0 ]] && die "failed to copy"

    passfile="${src%.ab}.passphrase.txt"
    if [[ -e "$passfile" ]]; then
        cp "$passfile" "$td/original.passphrase.txt"
    fi

    start "ls..."

    fixed_output "ls" "$src" "$td" \
                 ls "$td/original.ab"

    end

    start "ab2ab..."

    fixed_everything "ab2ab" "$src" "$td" "original.stripped.ab" \
                     ab2ab -d "$td/original.ab"

    fixed_everything "ab2ab-c" "$src" "$td" "compressed.ab" \
                     ab2ab -c "$td/original.stripped.ab" "$td/compressed.ab"

    fixed_everything "ab2ab-k" "$src" "$td" "stripped-k.ab" \
                     ab2ab -k "$td/original.ab" "$td/stripped-k.ab"

    fixed_output "ab2ab-e" "$src" "$td" \
                 ab2ab -e --output-passphrase=secret "$td/stripped-k.ab" "$td/encrypted.ab"

    end

    start "split and merge..."

    fixed_output "split" "$src" "$td" \
                 split "$td/original.ab"

    fixed_output "merge" "$src" "$td" \
                 merge "$td/hoardy_adb_split_"* "$td/merged.ab"

    equal_file "merge" "$td/original.stripped.ab" "$td/merged.ab"

    end

    start "unwrap and wrap..."

    fixed_everything "ab2tar" "$src" "$td" "original.tar" \
                     ab2tar "$td/original.ab"

    fixed_everything "tar2ab" "$src" "$td" "wrapped.ab" \
                     tar2ab --output-version=$oversion "$td/original.tar" "$td/wrapped.ab"

    equal_file "unwap-wrap" "$td/original.stripped.ab" "$td/wrapped.ab"

    end

    rm -rf "$td"
done

echo "total: $errors errors"
if ((errors > 0)); then
    exit 1
fi
