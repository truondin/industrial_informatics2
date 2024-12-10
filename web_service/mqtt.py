from datetime import datetime
import paho.mqtt.client as mqtt
import db
import json
import time
import threading

from web_service.objects import Measurement, State

GROUP_ID = 420
BROKER_IP = "34.255.214.243"

# Thresholds for alarm detection
THRESHOLD_X = 4  # 4 seconds (in seconds)
THRESHOLD_Y = 4  # 4 seconds (in seconds)

HIGH_THRESHOLD = 55
sensor_timers_x = {}  # Format: {sensor_id: start_time}
sensor_timers_y = {}  # Format: {sensor_id: start_time}
sensor_last_time = {}  # Format: {sensor_id: last_received_time}
sensor_flags_x = {}  # Format: {sensor_id: True/False}
sensor_flags_y = {}  # Format: {sensor_id: True/False}
sensor_thresholds = [20, 30, -1, 10, 15, 5, 20, 25, -5, 12]



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


def handle_measurement(sensor_id, measurement, timestamp):
    """ Save the sensor measurement in the database """
    print(f"sensor_id: {sensor_id} measurement: {str(measurement)}")
    if not db.sensor_exists(sensor_id):
        db.insert_sensor(sensor_id, 5, 15) # dummy low/high values

    state = get_sensor_state(sensor_id, measurement)
    measurement = Measurement(sensor_id, measurement, timestamp, state)

    db.insert_measurement(measurement)


def log_alarm(sensor_id, alarm_type, current_time):
    """ Log the alarm into the database """
    message = f"Sensor {sensor_id} exceeded {alarm_type}-level threshold."
    print(f"Logging alarm: {message}")
    db.insert_alarm(sensor_id, alarm_type, current_time, message)


def check_high(sensor_id, measurement, current_time):
    global sensor_thresholds, sensor_timers_x, sensor_timers_y, sensor_flags_x, sensor_flags_y
    if measurement > sensor_thresholds[sensor_id]:
        if sensor_id not in sensor_timers_x:
            sensor_timers_x[sensor_id] = current_time
            print(f"Threshold exceeded for sensor {sensor_id}. Timer X started.")
        if sensor_id not in sensor_timers_y:
            sensor_timers_y[sensor_id] = current_time
            print(f"Threshold exceeded for sensor {sensor_id}. Timer Y started.")
    else:
        # Reset timers and flags if the value drops below the threshold
        if sensor_id in sensor_timers_x:
            del sensor_timers_x[sensor_id]
            print(f"Timer X reset for sensor {sensor_id}.")
        if sensor_id in sensor_timers_y:
            del sensor_timers_y[sensor_id]
            print(f"Timer Y reset for sensor {sensor_id}.")
        if sensor_id in sensor_flags_x:
            sensor_flags_x[sensor_id] = False
        if sensor_id in sensor_flags_y:
            sensor_flags_y[sensor_id] = False


def check_timers():
    """Periodically check timers to handle cases where sensors stop sending data."""
    while True:
        current_time = datetime.now()
        for sensor_id in list(sensor_timers_x.keys()):
            elapsed_time_x = (current_time - sensor_timers_x[sensor_id]).seconds
            if elapsed_time_x >= THRESHOLD_X and not sensor_flags_x.get(sensor_id, False):
                sensor_flags_x[sensor_id] = True
                print(f"Flag X set for sensor {sensor_id}. Alarm triggered for X.")
                log_alarm(sensor_id, "HIGH-X", datetime.now())
                del sensor_timers_x[sensor_id]

        for sensor_id in list(sensor_timers_y.keys()):
            elapsed_time_y = (current_time - sensor_timers_y[sensor_id]).seconds
            if elapsed_time_y >= THRESHOLD_Y and not sensor_flags_y.get(sensor_id, False):
                sensor_flags_y[sensor_id] = True
                print(f"Flag Y set for sensor {sensor_id}. Alarm triggered for Y.")
                log_alarm(sensor_id, "HIGH-Y", datetime.now())
                del sensor_timers_y[sensor_id]

        time.sleep(0.5)  # Check every second/2


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
        print(f"{time} {measurement}")

        check_high(sensor_id, measurement, time)
        # Save the measurement in the database
        handle_measurement(sensor_id, measurement, time)

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

    threading.Thread(target=check_timers, daemon=True).start()

    try:
        rc = 0
        while rc == 0:
            rc = client.loop()
    finally:
        client.disconnect()
