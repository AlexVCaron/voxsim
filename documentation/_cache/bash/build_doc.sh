#!/usr/bin/env bash

TYPE=html
CWD=${PWD}
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"


if [[ "$#" -ne 1 ]]; then
    TYPE=$1
fi

cd ${DIR}/../..

make clean

make "$TYPE"

cd ${CWD}

exit
