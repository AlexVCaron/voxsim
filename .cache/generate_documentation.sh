#!/usr/bin/env bash

mkdir -p ../documentation

export SPHINX_APIDOC_OPTIONS=members,undoc-members,special-members,show-inheritance,synopsis

echo $SPHINX_APIDOC_OPTIONS

sphinx-apidoc -o ../documentation ../simulator -efFMa -H simulation_generator -A "Alex Valcourt Caron"

rm ../documentation/index.rst

cp doc/conf.py ../documentation/conf.py
cp -R doc/img ../documentation/img/
cp doc/index.rst ../documentation/index.rst
cp doc/install.rst ../documentation/install.rst
cp doc/api.rst ../documentation/api.rst
cp doc/architecture.rst ../documentation/architecture.rst
cp doc/concepts.rst ../documentation/concepts.rst

exit