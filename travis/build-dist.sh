#!/bin/bash
# Script is assumed to be running inside a manylinux container
# See https://github.com/pypa/manylinux

set -e -x

ls /opt/python/

# Compile wheels for each Python version
for PYBIN in /opt/python/cp3*/bin; do
  "${PYBIN}/pip" install -r /io/requirements.txt
  "${PYBIN}/pip" install -e /io/
  cd /io
  "${PYBIN}/python" setup.py sdist -d wheelhouse
  "${PYBIN}/pip" wheel /io/ -w wheelhouse/
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse/anonlink-*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w /io/wheelhouse/
done

# Install packages and test
for PYBIN in /opt/python/cp3*/bin; do
    "${PYBIN}/pip" install anonlink --no-index -f /io/wheelhouse
    (cd "$HOME"; "${PYBIN}/pytest" /io/tests -W ignore::DeprecationWarning)
done
