import mysql.connector
import time

# Database configurations for master and slaves
db_config_master = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'rootpassword',
    'database': 'mydb'
}

db_config_slave1 = db_config_master.copy()
db_config_slave1.update({'port': 3307})

db_config_slave2 = db_config_master.copy()
db_config_slave2.update({'port': 3308})


def connect_db(config):
    return mysql.connector.connect(**config)


def execute_query(connection, query, params=None):
    cursor = connection.cursor()
    cursor.execute(query, params or ())
    connection.commit()
    cursor.close()


def fetch_query(connection, query):
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result


def load_test():
    try:
        # Connect to master
        master_conn = connect_db(db_config_master)
        print("Connected to Master")

        # Create a test table if not exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS test_replication (
            id INT AUTO_INCREMENT PRIMARY KEY,
            data VARCHAR(255) NOT NULL
        )
        """
        execute_query(master_conn, create_table_query)

        # Insert data into master
        insert_data_query = "INSERT INTO test_replication (data) VALUES (%s)"
        test_data = [(f"Test data {i}",) for i in range(1, 11)]
        for data in test_data:
            execute_query(master_conn, insert_data_query, data)
            print(f"Inserted data: {data[0]}")

        # Allow some time for replication
        time.sleep(5)

        # Check data in slaves
        slave_connections = [connect_db(db_config_slave1), connect_db(db_config_slave2)]
        for i, slave_conn in enumerate(slave_connections, start=1):
            replicated_data = fetch_query(slave_conn, "SELECT * FROM test_replication")
            print(f"Data in Slave {i}: {replicated_data}")

            # Check if all rows are present
            if len(replicated_data) == len(test_data):
                print(f"Replication to Slave {i} is successful!")
            else:
                print(f"Replication to Slave {i} is incomplete.")

    finally:
        # Close all connections
        master_conn.close()
        for slave_conn in slave_connections:
            slave_conn.close()


# Run the load test
load_test()
