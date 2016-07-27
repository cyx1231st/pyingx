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

# clean up
apt-get purge rabbitmq-server
apt-get purge erlang*

# install
apt-get install rabbitmq-server

# config
sudo /usr/sbin/service rabbitmq-server restart

sudo rabbitmqctl add_user "$RABBIT_USERID" "$RABBIT_PASSWORD" ||
    { echo "failed to add user" 1>&2; return 1; }
sudo rabbitmqctl set_permissions "$RABBIT_USERID" ".*" ".*" ".*" ||
    { echo "failed to set permissions" 1>&2; return 1; }
sudo rabbitmqctl change_password $RABBIT_USERID $RABBIT_PASSWORD ||
    { echo "failed to change password" 1>&2; return 1; }

echo "rabbit://$RABBIT_USERID:$RABBIT_PASSWORD@$RABBIT_HOST:5672/"
