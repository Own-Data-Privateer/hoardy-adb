#!/usr/bin/env bash

root="https://github.com/Own-Data-Privateer/hoardy-adb"

set -e

sed -n "0,/^\[/ p" CHANGELOG.md | head -n -1 > CHANGELOG.new

{
    emit() {
        echo "## [$1] - $4" >&4

        if [[ -z $3 ]]; then
            echo "[$1]: $root/releases/tag/$2"
        else
            echo "[$1]: $root/compare/$3...$2"
        fi
    }

    prev=
    git tag --sort=-refname --sort=taggerdate --format '%(taggerdate:short) %(refname:short)' | while IFS= read -r -d $'\n' line ; do
        refname=${line##* }
        date=${line%% *}
        emit "$refname" "$refname" "$prev" "$date"
        prev="$refname"
    done
} 4> CHANGELOG.spine.rnew | tac >> CHANGELOG.new

{
    echo
    sed -n "/^# TODO/,$ p" CHANGELOG.md
} >> CHANGELOG.new

{
    echo "# Changelog"
    cat CHANGELOG.spine.rnew | tac
} >> CHANGELOG.spine.new
sed -n '/^# TODO/,$ d; /^##\? / p' CHANGELOG.md | sed 's/^\(## [^:]*\): .*/\1/g' > CHANGELOG.spine.old
diff -u CHANGELOG.spine.old CHANGELOG.spine.new || true
rm CHANGELOG.spine.*

mv CHANGELOG.new CHANGELOG.md
