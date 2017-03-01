#!/usr/bin/env bash
export PYTHONIOENCODING=UTF-8
export TEST_ENTITY_SERVICE="https://es.data61.xyz"

rm -fr venv
rm -fr build
python3.5 -m venv --clear venv
./venv/bin/pip install --upgrade pip coverage setuptools
./venv/bin/pip install -r requirements.txt
./venv/bin/python --version
./venv/bin/python setup.py test
./venv/bin/pip install -e .
./venv/bin/nosetests --with-xunit --with-coverage --cover-inclusive --cover-package=anonlink
./venv/bin/coverage html --omit="*/cpp_code/*" --omit="*build_matcher.py*"
