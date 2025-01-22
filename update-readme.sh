#!/bin/sh -e

{
    sed -n "/# What is/,/# Usage/ p" README.md
    echo

    python3 -m hoardy_adb.__main__ --help --markdown | sed '
s/^\(#\+\) /#\1 /
s/^\(#\+\) \(hoardy-adb[^A-Z[({]*\) [A-Z[({].*/\1 \2/
'

    ./test-cli.sh --help | sed '
s/^# usage: \(.*\)$/# Development: `\1`/
'
} > README.new
mv README.new README.md
pandoc -s -V pagetitle=README -f markdown -t html README.md > README.html
