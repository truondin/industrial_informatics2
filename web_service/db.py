import datetime
import sqlite3

from objects import Measurement

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
def insert_sensor(id, low, high):
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO sensors VALUES (:id, :low, :high)", {'id': id, 'low': low, 'high': high})


def insert_measurement(measurement: Measurement):
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO measurements VALUES (:id ,:sensor_id, :value, :time, :state)",
                  {'id': None,
                   'sensor_id': measurement.sensor_id,
                   'value': measurement.value,
                   'time': measurement.time,
                   'state': measurement.state.value})

def insert_alarm(sensor_id, alarm_level, timestamp, message):
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("""
        INSERT INTO alarms (sensor_id, alarm_level, timestamp, message)
        VALUES (:sensor_id, :alarm_level, :timestamp, :message)
        """, {'sensor_id': sensor_id, 'alarm_level': alarm_level, 'timestamp': timestamp, 'message': message})



def sensor_exists(sensor_id):
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sensors WHERE id = :id", {'id': sensor_id})
        count = c.fetchone()['COUNT(*)']  # Using dict_factory for row mapping
        return count > 0


def create_db():
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS sensors (
                     id INTEGER PRIMARY KEY,
                     low_threshold INTEGER,
                     high_threshold INTEGER
                     );""")

        c.execute("""CREATE TABLE IF NOT EXISTS measurements (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     sensor_id INTEGER,
                     value FLOAT,
                     time TIMESTAMP,
                     state INTEGER
                     );""")
        # Create alarms table
        c.execute("""CREATE TABLE IF NOT EXISTS alarms (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     sensor_id INTEGER,
                     alarm_level TEXT,
                     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                     message TEXT,
                     FOREIGN KEY(sensor_id) REFERENCES sensor(id)
                     );""")

        thresholds = [
            (5, 20),
            (-30, 30),
            (-7, -1),
            (-10, 10),
            (-5, 15),
            (-10, 5),
            (10, 20),
            (-15, 25),
            (-20, -5),
            (-8, 12)
        ]
        for i in range(len(thresholds)):
            low, high = thresholds[i]
            if not sensor_exists(i+1):
                insert_sensor(i+1, low, high)


def get_all_measurements():
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM measurements")
        return c.fetchall()


def get_measurements_by_sensor_id(sensor_id):
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM measurements WHERE sensor_id=:id ORDER BY time DESC", {'id': sensor_id})
        return c.fetchall()

def get_measurements_by_sensor_id_limit(sensor_id):
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM measurements WHERE sensor_id=:id ORDER BY time DESC LIMIT 25", {'id': sensor_id})
        return c.fetchall()

def get_all_sensors():
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM sensors")
        return c.fetchall()

def get_sensor(sensor_id):
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM sensors WHERE id=:id", {'id': sensor_id})
        return c.fetchone()


def get_measurements_in_time_range(start_time, end_time):
    start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        c = conn.cursor()
        query = """
        SELECT * FROM measurements
        WHERE time BETWEEN :start_time AND :end_time       
        ORDER BY time DESC
        """
        c.execute(query, {'start_time': start_time, 'end_time': end_time})
        return c.fetchall()


def get_measurements_until(date):
    date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        c = conn.cursor()
        query = """
        SELECT * FROM measurements
        WHERE time <= :date       
        ORDER BY time DESC
        """
        c.execute(query, {'date': date})
        return c.fetchall()


def get_measurements_from(date):
    date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        c = conn.cursor()
        query = """
        SELECT * FROM measurements
        WHERE time >= :date       
        ORDER BY time DESC
        """
        c.execute(query, {'date': date})
        return c.fetchall()


def get_measurements_of_sensor_in_time_range(sensor_id, start_time, end_time):
    start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        c = conn.cursor()
        query = """
        SELECT * FROM measurements
        WHERE sensor_id=:sensor_id AND time BETWEEN :start_time AND :end_time
        ORDER BY time DESC
        """
        c.execute(query, {'sensor_id': sensor_id, 'start_time': start_time, 'end_time': end_time})
        return c.fetchall()


def get_measurements_of_sensor_until(sensor_id, date):
    date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        c = conn.cursor()
        query = """
        SELECT * FROM measurements
        WHERE sensor_id=:sensor_id AND time <= :date
        ORDER BY time DESC
        """
        c.execute(query, {'sensor_id': sensor_id, 'date': date})
        return c.fetchall()


def get_measurements_of_sensor_from(sensor_id, date):
    date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        c = conn.cursor()
        query = """
        SELECT * FROM measurements
        WHERE sensor_id=:sensor_id AND time >= :date       
        ORDER BY time DESC
        """
        c.execute(query, {'sensor_id': sensor_id, 'date': date})
        return c.fetchall()


def count_measurements_of_sensor_in_time_range(sensor_id, start_time, end_time, state=None):
    start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        c = conn.cursor()
        if state is None:
            query = """
            SELECT COUNT(*) FROM measurements
            WHERE sensor_id=:sensor_id AND time BETWEEN :start_time AND :end_time
            """
            c.execute(query, {'sensor_id': sensor_id, 'start_time': start_time, 'end_time': end_time})
        else:
            query = """
            SELECT COUNT(*) FROM measurements
            WHERE sensor_id=:sensor_id AND state=:state AND time BETWEEN :start_time AND :end_time
            """
            c.execute(query, {'sensor_id': sensor_id, 'state': state.value, 'start_time': start_time, 'end_time': end_time})
        count = c.fetchone()['COUNT(*)']
        return count


def get_alarms_by_sensor_id(sensor_id):
    with _get_connection() as conn:
        c = conn.cursor()
        c.execute("""
        SELECT * FROM alarms
        WHERE sensor_id=:sensor_id
        ORDER BY timestamp DESC
        """, {'sensor_id': sensor_id})
        return c.fetchall()

def get_alarms_in_time_range(sensor_id, from_date, to_date):
    from_date = datetime.datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S")
    to_date = datetime.datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        c = conn.cursor()
        query = """
        SELECT * FROM alarms
        WHERE sensor_id=:sensor_id AND timestamp BETWEEN :from_date AND :to_date
        ORDER BY timestamp DESC
        """
        c.execute(query, {'sensor_id': sensor_id, 'from_date': from_date, 'to_date': to_date})
        return c.fetchall()

