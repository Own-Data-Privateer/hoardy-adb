#!/bin/sh -e

black $1 *.py hoardy_adb
mypy
#pytest -k 'not slow'
pylint *.py hoardy_adb
./update-readme.sh
