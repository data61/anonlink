#!/bin/bash
set -e -x

yum install -y atlas-devel

# Compile wheels
for PYBIN in /opt/python/cp37-cp37m/bin; do
    "${PYBIN}/pip" install -r /io/requirements.txt
    "${PYBIN}/pip" install -e /io/
    "${PYBIN}/pip" wheel /io/ -w wheelhouse/
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse/anonlink-*.whl; do
    auditwheel repair "$whl" -w /io/wheelhouse/
done

# Install packages and test
for PYBIN in /opt/python/cp37-cp37m/bin/; do
    "${PYBIN}/pip" install anonlink --no-index -f /io/wheelhouse
    (cd "$HOME"; "${PYBIN}/pytest" /io/tests)
done
