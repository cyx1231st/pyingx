#!/bin/bash
set -x
TOP_DIR=$(cd $(dirname "$0") && pwd)
pushd $TOP_DIR > /dev/null

virtualenv venv_dev
source ./venv_dev/bin/activate
python setup.py develop
sudo mkdir /etc/pyingx
sudo cp ./etc/* /etc/pyingx/
# ln -sf $TOP_DIR/../pyingx ~/pyingx

popd > /dev/null
