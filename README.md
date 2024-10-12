# Mysql replication

## Getting started
Starting docker compose with 1 mysql master and 2 replicas
```
docker compose up
```

## How to verify replication
1. Connect to the Master:

```bash
docker exec -it mysql-master mysql -u root -p
Enter rootpassword when prompted.
```

2. Create Database and Table:

```sql
CREATE DATABASE mydb;
USE mydb;

CREATE TABLE test_table (
  id INT NOT NULL AUTO_INCREMENT,
  data VARCHAR(100),
  PRIMARY KEY (id)
);
```

3. Insert Test Data into master

```sql
INSERT INTO test_table (data) VALUES ('Replication test 1');
INSERT INTO test_table (data) VALUES ('Replication test 2');
```

Exit the MySQL Shell:
```sql
EXIT;
```

4. Check Inserted Data are Replicated to Slaves:
For Slave 1:

```bash
docker exec -it mysql-slave-1 mysql -u root -p -e "SELECT * FROM mydb.test_table;"
Enter rootpassword when prompted.
```

For Slave 2:
```bash
docker exec -it mysql-slave-2 mysql -u root -p -e "SELECT * FROM mydb.test_table;"
Enter rootpassword when prompted.
```

5. Verify Expected Output on Both Slaves:
```bash
+----+--------------------+
| id | data               |
+----+--------------------+
|  1 | Replication test 1 |
|  2 | Replication test 2 |
+----+--------------------+
If the data appears on both slaves, replication is functioning correctly.
```
