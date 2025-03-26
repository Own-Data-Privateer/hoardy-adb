#!/bin/sh -e

echo '$table-of-contents$' > toc.template
for i in 0 1; do
{
    echo "# Table of Contents"
    echo "<details><summary>(Click me to see it.)</summary>"
    pandoc --wrap=none --toc --template=toc.template --metadata title=toc -f markdown -t html README.md \
        | sed '/Table of Contents/ d'
    echo "</details>"
    echo

    sed -n "/# What is/,/# Usage/ p" README.md
    echo

    python3 -m hoardy_adb --help --markdown | sed '
s/^\(#\+\) /#\1 /
s/^\(#\+\) \(hoardy-adb[^A-Z[({]*\) [A-Z[({].*/\1 \2/
'

    echo

    ./test-hyadb.sh --help | sed '
s/^# usage: \(.*\)$/# Development: `\1`/
'
} > README.new
mv README.new README.md
done
pandoc -V pagetitle=README -f markdown -t html README.md > README.html
