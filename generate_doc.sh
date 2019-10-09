#!/usr/bin/env bash

mkdir -p documentation

export SPHINX_APIDOC_OPTIONS=members,undoc-members,show-inheritance,private-members

echo $SPHINX_APIDOC_OPTIONS

sphinx-apidoc -o documentation simulator -e --implicit-namespaces -F -a -H simulation_generator -A "Alex Valcourt Caron"

cp documentation/cache/conf.py documentation/conf.py

exit