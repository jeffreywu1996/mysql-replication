#!/bin/bash
set -e

echo "Slave 1: Waiting for master to be ready..."
until mysqladmin ping -h mysql-master --silent; do
  sleep 1
done

echo "Slave 1: Waiting for replication user to be ready..."
until mysql -h mysql-master -u repl -preplpassword -e "SELECT 1" &> /dev/null; do
  sleep 1
done

echo "Slave 1: Setting up replication..."

mysql -uroot -p${MYSQL_ROOT_PASSWORD} <<EOSQL
CHANGE REPLICATION SOURCE TO
  SOURCE_HOST='mysql-master',
  SOURCE_USER='repl',
  SOURCE_PASSWORD='replpassword',
  SOURCE_AUTO_POSITION=1;
START REPLICA;
EOSQL

echo "Slave 1: Replication setup completed."
