#!/bin/bash
set -x
TOP_DIR=$(cd $(dirname "$0") && pwd)
pushd $TOP_DIR > /dev/null

sudo python setup.py develop
ln -sf $TOP_DIR/../pyingx ~/pyingx

popd > /dev/null
