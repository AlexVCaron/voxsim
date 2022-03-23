#!/usr/bin/env bash

CWD=${PWD}
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd ${DIR}/../..

shopt -s extglob
rm -rf !(_cache|_cache/*)
cd _cache

export SPHINX_APIDOC_OPTIONS=members,undoc-members,special-members,show-inheritance,synopsis

sphinx-apidoc -o .. ../../simulator -efFMa -H simulation_generator -A "Alex Valcourt Caron"

rm ../index.rst

cp conf.py ../conf.py
cp -R img ../img/
cp index.rst ../index.rst
cp install.rst ../install.rst
cp api.rst ../api.rst
cp architecture.rst ../architecture.rst
cp concepts.rst ../concepts.rst

cd ${CWD}

exit
