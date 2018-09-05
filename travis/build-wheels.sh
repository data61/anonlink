#!/bin/bash
set -e -x

# Install any system packages required by our library
#yum install -y <package-name>

# Compile wheels
for PYBIN in /opt/python/*/bin; do
    "${PYBIN}/pip" install -r /io/dev-requirements.txt
    "${PYBIN}/pip" wheel /io/ -w wheelhouse/
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    auditwheel repair "$whl" -w /io/wheelhouse/
done

# Install packages and test
for PYBIN in /opt/python/*/bin/; do
    "${PYBIN}/pip" install anonlink --no-index -f /io/wheelhouse
    (cd "$HOME"; "${PYBIN}/pytest" anonlink)
done