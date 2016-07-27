#!/bin/bash
set -o xtrace
unset GREP_OPTIONS
set -o nounset
umask 022

MYSQL_USER=root
MYSQL_HOST=127.0.0.1
MYSQL_PASSWORD=123456

BASE_SQL_CONN=mysql+pymysql://$MYSQL_USER:$MYSQL_PASSWORD@$MYSQL_HOST

source ./ini-config

function apt-get {
    local result
    sudo apt-get --option "Dpkg::Options::=--force-confold" --assume-yes "$@" < /dev/null
    result=$?
    echo $result
    return $result
}

function stop_service {
    sudo /usr/sbin/service $1 stop
}

function start_service {
    sudo /usr/sbin/service $1 start
}

function restart_service {
    sudo /usr/sbin/service $1 restart
}

# clean up
apt-get purge mysql* mariadb*
sudo rm -rf /var/lib/mysql
sudo rm -rf /etc/mysql

# install
sudo debconf-set-selections <<EOF
mysql-server mysql-server/root_password password $MYSQL_PASSWORD
mysql-server mysql-server/root_password_again password $MYSQL_PASSWORD
mysql-server mysql-server/start_on_boot boolean true
EOF

if [[ ! -e $HOME/.my.cnf ]]; then
    cat <<EOF >$HOME/.my.cnf
[client]
user=$MYSQL_USER
password=$MYSQL_PASSWORD
host=$MYSQL_HOST
EOF
fi
chmod 0600 $HOME/.my.cnf

apt-get install mysql-server
start_service mysql

# config
sudo mysql -uroot -p$MYSQL_PASSWORD -h127.0.0.1 -e "GRANT ALL PRIVILEGES ON *.* TO '$MYSQL_USER'@'%' identified by '$MYSQL_PASSWORD';"

my_conf=/etc/mysql/my.cnf
iniset -sudo $my_conf mysqld bind-address 0.0.0.0
iniset -sudo $my_conf mysqld sql_mode STRICT_ALL_TABLES
iniset -sudo $my_conf mysqld default-storage-engine InnoDB
iniset -sudo $my_conf mysqld max_connections 1024
iniset -sudo $my_conf mysqld query_cache_type OFF
iniset -sudo $my_conf mysqld query_cache_size 0

restart_service mysql

sudo pip install PyMySQL
sudo pip install SQLAlchemy

# echo configuration
echo "$BASE_SQL_CONN/mysql?charset=utf8"
