from datetime import datetime
import paho.mqtt.client as mqtt
import db
import json
import time
import threading

from objects import Measurement, State

GROUP_ID = 420
BROKER_IP = "34.255.214.243"

# Time thresholds for alarm detection (in seconds)
THRESHOLD_HIGH = 4
THRESHOLD_LOW = 4

# Global dictionary which contains {sensor_id: True/False} for deciding whether to create new thread for alarm timer
sensor_alarm_timer_running = {}


# Get the sensor state based on the value
def get_sensor_state(sensor_id, value):
    sensor = db.get_sensor(sensor_id)
    low = sensor['low_threshold']
    high = sensor['high_threshold']
    if value < low:
        return State.LOW
    elif value > high:
        return State.HIGH
    else:
        return State.NORMAL


# Handle the incoming sensor measurement
def handle_measurement(sensor_id, measurement, timestamp, state):
    """ Save the sensor measurement in the database """
    print(f"sensor_id: {sensor_id} measurement: {str(measurement)}")
    if not db.sensor_exists(sensor_id):
        db.insert_sensor(sensor_id, 5, 15)  # dummy low/high values

    measurement = Measurement(sensor_id, measurement, timestamp, state)

    db.insert_measurement(measurement)


# Log the alarm into the database
def log_alarm(sensor_id, alarm_type, current_time):
    """ Log the alarm into the database """
    message = f"Sensor {sensor_id} exceeded {alarm_type}-level threshold."
    print(f"Logging alarm: {message}")
    db.insert_alarm(sensor_id, alarm_type, current_time, message)


def check_timers_alarm(sensor_id, timestamp, state, time_threshold):
    print(f"Starting alarm timer on thread: {threading.current_thread().name}")
    sensor_alarm_timer_running[sensor_id] = True
    time.sleep(time_threshold)
    latest_measurement = db.get_latest_measurement_by_sensor_id(sensor_id)
    latest_state = State(latest_measurement['state'])
    print(f"Alarm timer ended - latest measurement state: {latest_state}")
    if latest_state == state:
        log_alarm(sensor_id, state.name, timestamp)
    sensor_alarm_timer_running[sensor_id] = False


def handle_alarm(sensor_id, timestamp, state):
    if sensor_id not in sensor_alarm_timer_running.keys():
        sensor_alarm_timer_running[sensor_id] = False
    print(f"Handle alarm on thread: {threading.current_thread().name}")

    if not sensor_alarm_timer_running[sensor_id]:
        if state == State.HIGH:
            threading.Thread(
                target=check_timers_alarm,
                args=(sensor_id, timestamp, state, THRESHOLD_HIGH),
                daemon=True
            ).start()
        elif state == State.LOW:
            threading.Thread(
                target=check_timers_alarm,
                args=(sensor_id, timestamp, state, THRESHOLD_LOW),
                daemon=True
            ).start()


# MQTT on_message handler
def on_message(client, userdata, msg):
    """ Handle incoming MQTT messages """
    print("Got some MQTT message ")
    sensor_id = msg.topic.split('/')[-1]
    payload = msg.payload.decode('utf-8')

    try:
        msg_data = json.loads(payload)
        print(msg_data)
        measurement = msg_data['value']
        timestamp = msg_data['timestamp']

        # Convert timestamp string to datetime
        format_string = "%Y-%m-%d %H:%M:%S"
        time = datetime.strptime(timestamp, format_string)
        state = get_sensor_state(sensor_id, measurement)
        print(f"New info: {time} sensor: {sensor_id} measurement: {measurement} - {state}")

        handle_alarm(sensor_id, time, state)
        # Save the measurement in the database
        handle_measurement(sensor_id, measurement, time, state)

    except ValueError:
        print(f"Error: Invalid payload {payload} - expecting float")


# MQTT subscription thread
def start_subscription():
    """ Start the MQTT subscription thread """
    print("MQTT subscription started....")
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER_IP)
    client.subscribe("ii24/" + str(GROUP_ID) + "/sensor/#")  # Subscribe to all sensors

    try:
        rc = 0
        while rc == 0:
            rc = client.loop()
    finally:
        client.disconnect()
