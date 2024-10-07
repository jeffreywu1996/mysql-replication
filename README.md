# Mysql replication

## Getting started
```
docker compose up


Verify



Connect to the Master:

bash
Copy code
docker exec -it mysql-master mysql -u root -p
Enter rootpassword when prompted.

Create Database and Table:

sql
Copy code
CREATE DATABASE mydb;
USE mydb;

CREATE TABLE test_table (
  id INT NOT NULL AUTO_INCREMENT,
  data VARCHAR(100),
  PRIMARY KEY (id)
);
Insert Data:

sql
Copy code
INSERT INTO test_table (data) VALUES ('Replication test 1');
INSERT INTO test_table (data) VALUES ('Replication test 2');
Exit the MySQL Shell:

sql
Copy code
EXIT;
Check Data on Slaves:

For Slave 1:

bash
Copy code
docker exec -it mysql-slave-1 mysql -u root -p -e "SELECT * FROM mydb.test_table;"
For Slave 2:

bash
Copy code
docker exec -it mysql-slave-2 mysql -u root -p -e "SELECT * FROM mydb.test_table;"
Enter rootpassword when prompted.

Expected Output on Both Slaves:

bash
Copy code
+----+--------------------+
| id | data               |
+----+--------------------+
|  1 | Replication test 1 |
|  2 | Replication test 2 |
+----+--------------------+
If the data appears on both slaves, replication is functioning correctly.
```
