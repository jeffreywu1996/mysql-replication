# load_test.py
from locust import User, task, between
import mysql.connector
import time
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define database configurations at the global scope
db_config_master = {
    'host': 'localhost',
    'port': 3306,
    'user': 'user',
    'password': 'password',
    'database': 'mydb'
}

db_config_slave1 = db_config_master.copy()
db_config_slave1.update({'port': 3307})

db_config_slave2 = db_config_master.copy()
db_config_slave2.update({'port': 3308})


class MySQLLoadTest(User):
    wait_time = between(1, 2)  # Adjust timing for load intervals

    def on_start(self):
        # Establish database connections
        self.master_conn = self.connect_db(db_config_master)
        self.slave_conns = [
            self.connect_db(db_config_slave1),
            self.connect_db(db_config_slave2)
        ]

        # Create test table
        self.execute_query(self.master_conn, """
            CREATE TABLE IF NOT EXISTS mydb (
                id INT AUTO_INCREMENT PRIMARY KEY,
                data VARCHAR(255) NOT NULL
            )
        """)

    def connect_db(self, config):
        try:
            return mysql.connector.connect(**config)
        except mysql.connector.Error as err:
            logger.error(f"Error connecting to database: {err}")
            return None

    def execute_query(self, connection, query, params=None):
        cursor = connection.cursor()
        cursor.execute(query, params or ())
        connection.commit()
        cursor.close()

    def fetch_query(self, connection, query):
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result

    @task
    def insert_data(self):
        start_time = time.time()
        try:
            insert_query = "INSERT INTO test_replication (data) VALUES (%s)"
            test_data = f"Test data {time.time()}"
            self.execute_query(self.master_conn, insert_query, (test_data,))
            logger.info(f"Inserted data: {test_data}")
            time.sleep(2)  # Give some time for replication

            # Check replication on slaves
            for i, slave_conn in enumerate(self.slave_conns, start=1):
                replicated_data = self.fetch_query(
                    slave_conn,
                    "SELECT * FROM test_replication ORDER BY id DESC LIMIT 1"
                )
                if replicated_data and replicated_data[0][1] == test_data:
                    logger.info(f"Replication successful on Slave {i}")
                else:
                    logger.warning(f"Replication delayed or failed on Slave {i}")

            total_time = int((time.time() - start_time) * 1000)  # Convert to ms

            # Fire request event for success
            self.environment.events.request.fire(
                request_type="db",
                name="insert_data",
                response_time=total_time,
                response_length=0,
                exception=None  # No exception implies success
            )
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)

            # Fire request event for failure
            self.environment.events.request.fire(
                request_type="db",
                name="insert_data",
                response_time=total_time,
                response_length=0,
                exception=e  # Exception implies failure
            )
            logger.error(f"Error during insert_data: {e}")
            traceback.print_exc()

    def on_stop(self):
        # Close master connection
        if self.master_conn:
            self.master_conn.close()
            logger.info("Master DB connection closed.")
        # Close slave connections
        for idx, conn in enumerate(self.slave_conns, start=1):
            if conn:
                conn.close()
                logger.info(f"Slave {idx} DB connection closed.")
