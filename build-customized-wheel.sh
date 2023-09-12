#!/usr/bin/env bash

set -eu

UNREPAIRED_WHEELS=/tmp/wheels

# Compile wheels
SUPPORT_PY_VERSIONS=(cp38-cp38 cp39-cp39 cp310-cp310 cp311-cp311)
for PY_VERSION in ${SUPPORT_PY_VERSIONS[@]}; do
    echo "working on ${PY_VERSION}"
    PYBIN=/opt/python/${PY_VERSION}/bin/python
    PATH=${PYBIN}:$PATH
    ${PYBIN} setup.py bdist_wheel -d ${UNREPAIRED_WHEELS}
done

# Bundle GEOS into the wheels
for whl in ${UNREPAIRED_WHEELS}/*.whl; do
    auditwheel repair ${whl} -w dist
done
