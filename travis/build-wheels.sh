#!/bin/bash
set -e -x

yum install -y atlas-devel

# Compile wheels
export PYBIN="/opt/python/cp37-cp37m/bin"

"${PYBIN}/pip" install -r /io/requirements.txt
"${PYBIN}/pip" install -e /io/
"${PYBIN}/pip" wheel /io/ -w wheelhouse/

# Bundle external shared libraries into the wheels
for whl in wheelhouse/anonlink-*.whl; do
    auditwheel repair "$whl" -w /io/wheelhouse/
done

# Install packages and test
"${PYBIN}/pip" install anonlink --no-index -f /io/wheelhouse
(cd "$HOME"; "${PYBIN}/pytest" /io/tests)
