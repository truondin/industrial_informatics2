from datetime import datetime
import paho.mqtt.client as mqtt
import db
import json
import time
import threading

from objects import Measurement, State

GROUP_ID = 420
BROKER_IP = "34.255.214.243"

# Thresholds for alarm detection
THRESHOLD_X = 4  # Threshold for HIGH level (in seconds)
THRESHOLD_Y = 4  # Threshold for LOW level (in seconds)

sensor_timers_x = {}  # Format: {sensor_id: start_time} (for HIGH)
sensor_timers_y = {}  # Format: {sensor_id: start_time} (for LOW)
sensor_last_time = {}  # Format: {sensor_id: last_received_time}
sensor_flags_x = {}  # Format: {sensor_id: True/False} (for HIGH)
sensor_flags_y = {}  # Format: {sensor_id: True/False} (for LOW)
sensor_high_thresholds = [20, 30, -1, 10, 15, 5, 20, 25, -5, 12]
sensor_low_thresholds = [5, -30, -7, -10, -5, -10, 10, -15, -20, -8]

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

# Check if the sensor's value exceeds the HIGH threshold
def check_high(sensor_id, measurement, current_time):
    global sensor_high_thresholds, sensor_timers_x, sensor_timers_y, sensor_flags_x, sensor_flags_y
    if measurement > sensor_high_thresholds[sensor_id]:  # High threshold check
        if sensor_id not in sensor_timers_x:
            sensor_timers_x[sensor_id] = current_time
            print(f"Threshold exceeded for sensor {sensor_id}. Timer X started.")
    else:
        # Reset timers and flags if the value drops below the threshold
        if sensor_id in sensor_timers_x:
            del sensor_timers_x[sensor_id]
            print(f"Timer X reset for sensor {sensor_id}.")
        if sensor_id in sensor_flags_x:
            sensor_flags_x[sensor_id] = False

# Check if the sensor's value falls below the LOW threshold
def check_low(sensor_id, measurement, current_time):
    global sensor_low_thresholds, sensor_timers_y, sensor_flags_y
    low_threshold = sensor_low_thresholds[sensor_id]  # Use the specific low threshold for this sensor
    if measurement < low_threshold:  # Low threshold check
        if sensor_id not in sensor_timers_y:
            sensor_timers_y[sensor_id] = current_time
            print(f"Low threshold exceeded for sensor {sensor_id}. Timer Y started.")
    else:
        # Reset timers and flags if the value rises above the low threshold
        if sensor_id in sensor_timers_y:
            del sensor_timers_y[sensor_id]
            print(f"Timer Y reset for sensor {sensor_id}.")
        if sensor_id in sensor_flags_y:
            sensor_flags_y[sensor_id] = False

# Periodically check timers to handle alarms
def check_timers():
    """Periodically check timers to handle cases where sensors stop sending data."""
    while True:
        current_time = datetime.now()
        # Check high alarms
        for sensor_id in list(sensor_timers_x.keys()):
            elapsed_time_x = (current_time - sensor_timers_x[sensor_id]).seconds
            if elapsed_time_x >= THRESHOLD_X and not sensor_flags_x.get(sensor_id, False):
                sensor_flags_x[sensor_id] = True
                print(f"Flag X set for sensor {sensor_id}. Alarm triggered for X.")
                log_alarm(sensor_id, "HIGH", datetime.now())
                del sensor_timers_x[sensor_id]

        # Check low alarms
        for sensor_id in list(sensor_timers_y.keys()):
            elapsed_time_y = (current_time - sensor_timers_y[sensor_id]).seconds
            if elapsed_time_y >= THRESHOLD_Y and not sensor_flags_y.get(sensor_id, False):
                sensor_flags_y[sensor_id] = True
                print(f"Flag Y set for sensor {sensor_id}. Alarm triggered for Y.")
                log_alarm(sensor_id, "LOW", datetime.now())
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
        state = get_sensor_state(sensor_id, measurement)
        check_high(int(sensor_id)-1, measurement, time)  # Check for high alarms
        check_low(int(sensor_id)-1, measurement, time)   # Check for low alarms
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

    threading.Thread(target=check_timers, daemon=True).start()

    try:
        rc = 0
        while rc == 0:
            rc = client.loop()
    finally:
        client.disconnect()
