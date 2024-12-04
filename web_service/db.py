import datetime
import sqlite3

DB_NAME = "database.db"


def _dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def _get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = _dict_factory
    return conn


# CREATE
def insert_sensor(id):
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO sensor VALUES (:id)", {'id': id})


def insert_measurement(sensor_id, value):
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO measurement VALUES (:id ,:sensor_id, :value, :time)",
                  {'id': None, 'sensor_id': sensor_id, 'value': value, 'time': datetime.datetime.now()})


def sensor_exists(sensor_id):
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sensor WHERE id = :id", {'id': sensor_id})
        count = c.fetchone()['COUNT(*)']  # Using dict_factory for row mapping
        return count > 0


def create_db():
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS sensor (
                     id INTEGER PRIMARY KEY
                     );""")

        c.execute("""CREATE TABLE IF NOT EXISTS measurement (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     sensor_id INTEGER,
                     value FLOAT,
                     time TIMESTAMP
                     );""")


def get_all_measurements():
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM measurement")
        return c.fetchall()


def get_all_sensors():
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM sensors")
        return c.fetchall()


def get_measurements_in_time_range(start_time, end_time):
    with _get_connection() as conn:
        c = conn.cursor()
        query = """
        SELECT * FROM measurement
        WHERE time BETWEEN :start_time AND :end_time
        """
        c.execute(query, {'start_time': start_time, 'end_time': end_time})
        return c.fetchall()