#!/usr/bin/env bash

mkdir -p documentation

export SPHINX_APIDOC_OPTIONS=members,undoc-members,special-members,show-inheritance,synopsis

echo $SPHINX_APIDOC_OPTIONS

sphinx-apidoc -o documentation simulator -efFMa -H simulation_generator -A "Alex Valcourt Caron"

rm documentation/index.rst

cp documentation/_cache/conf.py documentation/conf.py
cp -R documentation/_cache/img documentation/img/
cp documentation/_cache/index.rst documentation/index.rst
cp documentation/_cache/install.rst documentation/install.rst
cp documentation/_cache/api.rst documentation/api.rst
cp documentation/_cache/architecture.rst documentation/architecture.rst
cp documentation/_cache/concepts.rst documentation/concepts.rst

exit