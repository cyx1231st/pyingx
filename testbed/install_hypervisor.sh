#!/bin/bash
set -o xtrace
unset GREP_OPTIONS
set -o nounset
umask 022

RABBIT_USERID=rabbituser
RABBIT_PASSWORD=123456

function apt-get {
    local result
    sudo apt-get --option "Dpkg::Options::=--force-confold" --assume-yes "$@" < /dev/null
    result=$?
    echo $result
    return $result
}

# install
apt-get install pkg-config qemu-kvm libguestfs0 libvirt-bin libvirt-dev
sudo pip install libvirt-python

# config
log_filters="1:libvirt 1:qemu 1:conf 1:security 3:object 3:event 3:json 3:file 1:util 1:cpu"
log_outputs="1:file:/var/log/libvirt/libvirtd.log"
if ! sudo grep -q "^log_filters=\"$log_filters\"" /etc/libvirt/libvirtd.conf; then
    echo "log_filters=\"$log_filters\"" | sudo tee -a /etc/libvirt/libvirtd.conf
fi
if ! sudo grep -q "^log_outputs=\"$log_outputs\"" /etc/libvirt/libvirtd.conf; then
    echo "log_outputs=\"$log_outputs\"" | sudo tee -a /etc/libvirt/libvirtd.conf
fi

sudo /usr/sbin/service libvirt-bin restart
