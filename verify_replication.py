import mysql.connector
from mysql.connector import Error
import time
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Configuration for Master and Slaves
MASTER_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'rootpassword',
    'database': 'mydb'
}

SLAVES_CONFIG = [
    {
        'name': 'Slave 1',
        'host': 'localhost',
        'port': 3307,
        'user': 'root',
        'password': 'rootpassword',
        'database': 'mydb'
    },
    {
        'name': 'Slave 2',
        'host': 'localhost',
        'port': 3308,
        'user': 'root',
        'password': 'rootpassword',
        'database': 'mydb'
    }
]

TEST_TABLE = 'test_table'
TEST_DATA = 'Replication test entry'

def connect_db(config):
    """
    Establish a connection to the MySQL database.
    """
    try:
        connection = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        if connection.is_connected():
            logging.info(f"Connected to {config['host']}:{config['port']} successfully.")
            return connection
    except Error as e:
        logging.error(f"Error connecting to {config['host']}:{config['port']} - {e}")
    return None

def check_replication_status(slave_conn, slave_name):
    """
    Check the replication status of a slave.
    """
    try:
        cursor = slave_conn.cursor(dictionary=True)
        cursor.execute("SHOW REPLICA STATUS;")
        status = cursor.fetchone()
        if not status:
            logging.warning(f"{slave_name}: No replication status available.")
            return False

        io_running = status.get('Replica_IO_Running')
        sql_running = status.get('Replica_SQL_Running')
        seconds_behind = status.get('Seconds_Behind_Master')

        if io_running == 'Yes' and sql_running == 'Yes':
            logging.info(f"{slave_name}: Replication is running smoothly. Seconds behind master: {seconds_behind}")
            return True
        else:
            logging.error(f"{slave_name}: Replication issues detected.")
            logging.error(f"    Replica_IO_Running: {io_running}")
            logging.error(f"    Replica_SQL_Running: {sql_running}")
            logging.error(f"    Seconds_Behind_Master: {seconds_behind}")
            return False
    except Error as e:
        logging.error(f"{slave_name}: Error checking replication status - {e}")
        return False
    finally:
        cursor.close()

def insert_test_data(master_conn):
    """
    Insert a test record into the master database.
    """
    try:
        cursor = master_conn.cursor()
        # Ensure test_table exists
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TEST_TABLE} (
                id INT NOT NULL AUTO_INCREMENT,
                data VARCHAR(255),
                PRIMARY KEY (id)
            );
        """)
        # Insert test data
        cursor.execute(f"INSERT INTO {TEST_TABLE} (data) VALUES (%s);", (TEST_DATA,))
        master_conn.commit()
        logging.info(f"Inserted test data into master: '{TEST_DATA}'")
    except Error as e:
        logging.error(f"Error inserting test data into master - {e}")
    finally:
        cursor.close()

def verify_test_data_on_slave(slave_conn, slave_name):
    """
    Verify that the test record exists on the slave database.
    """
    try:
        cursor = slave_conn.cursor()
        cursor.execute(f"SELECT data FROM {TEST_TABLE} WHERE data = %s;", (TEST_DATA,))
        result = cursor.fetchone()
        if result:
            logging.info(f"{slave_name}: Test data verified successfully.")
            return True
        else:
            logging.error(f"{slave_name}: Test data not found.")
            return False
    except Error as e:
        logging.error(f"{slave_name}: Error verifying test data - {e}")
        return False
    finally:
        cursor.close()

def main():
    # Connect to Master
    master_conn = connect_db(MASTER_CONFIG)
    if not master_conn:
        logging.critical("Failed to connect to master. Exiting.")
        sys.exit(1)

    # Connect to Slaves
    slave_conns = []
    for slave in SLAVES_CONFIG:
        conn = connect_db(slave)
        if conn:
            slave_conns.append((slave['name'], conn))
        else:
            logging.warning(f"{slave['name']}: Unable to establish connection.")

    if not slave_conns:
        logging.critical("No slaves connected. Exiting.")
        master_conn.close()
        sys.exit(1)

    # Check replication status on each slave
    replication_ok = True
    for slave_name, conn in slave_conns:
        status = check_replication_status(conn, slave_name)
        if not status:
            replication_ok = False

    if not replication_ok:
        logging.error("Replication status check failed on one or more slaves.")
    else:
        logging.info("All slaves are replicating correctly.")

    # Insert test data on master
    insert_test_data(master_conn)

    # Wait for replication to catch up
    logging.info("Waiting for replication to propagate test data...")
    time.sleep(10)  # Adjust as necessary based on your environment

    # Verify test data on slaves
    data_ok = True
    for slave_name, conn in slave_conns:
        exists = verify_test_data_on_slave(conn, slave_name)
        if not exists:
            data_ok = False

    if data_ok:
        logging.info("Data consistency check passed on all slaves.")
    else:
        logging.error("Data consistency check failed on one or more slaves.")

    # Close all connections
    master_conn.close()
    for _, conn in slave_conns:
        conn.close()

    if replication_ok and data_ok:
        logging.info("Master-Slave replication verification completed successfully.")
    else:
        logging.warning("Master-Slave replication verification encountered issues.")

if __name__ == "__main__":
    main()
