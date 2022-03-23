#!/usr/bin/env bash

if [ ! -d documentation ]
then
  cd .cache
  ./generate_documentation.sh
  cd ..
fi

cd documentation
make html
