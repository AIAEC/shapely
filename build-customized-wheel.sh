#!/usr/bin/env bash

set -eu

ORIGINAL_PATH=$PATH
UNREPAIRED_WHEELS=/tmp/wheels

# Compile wheels
for PYBIN in /opt/python/cp3*/bin; do
    PATH=${PYBIN}:$ORIGINAL_PATH
    ${PYBIN}/python3 setup.py bdist_wheel -d ${UNREPAIRED_WHEELS}
done

# Bundle GEOS into the wheels
for whl in ${UNREPAIRED_WHEELS}/*.whl; do
    auditwheel repair ${whl} -w dist
done

# build source distribution using python3.10
/opt/python/cp310-cp310/bin/python3 setup.py sdist
