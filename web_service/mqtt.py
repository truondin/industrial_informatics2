from datetime import datetime
import paho.mqtt.client as mqtt
import db
import json

GROUP_ID = 420
BROKER_IP = "34.255.214.243"

# Thresholds for alarm detection
THRESHOLD_X = 4  # 4 seconds (in seconds)
THRESHOLD_Y = 4  # 4 seconds (in seconds)

# Dictionaries to track sensor states and alarm configurations
sensor_states = {}  # Format: {sensor_id: {"state": "HIGH/LOW/NORMAL", "timestamp": datetime}}
sensor_alarm_values = {}  # Format: {sensor_id: {"HIGH": high_value, "LOW": low_value}}
sensor_send_alarm = {}  # Format: {sensor_id: {"send": 0/1, "alarm": "HIGH/LOW", "type": "X/Y"}}

def save_in_db(sensor_id, measurement, timestamp):
    """ Save the sensor measurement in the database """
    print(f"sensor_id: {sensor_id} measurement: {str(measurement)}")
    if not db.sensor_exists(sensor_id):
        db.insert_sensor(sensor_id)
    db.insert_measurement(sensor_id, measurement, timestamp)

def log_alarm(sensor_id, alarm_type, current_time):
    """ Log the alarm into the database """
    message = f"Sensor {sensor_id} exceeded {alarm_type}-level threshold."
    print(f"Logging alarm: {message}")
    db.insert_alarm(sensor_id, alarm_type, current_time, message)

def set_sensor_state(sensor_id, value, current_time):
    """ Determine and set the state of the sensor based on its value """
    global sensor_states

    # Initialize the sensor state if not already done
    if sensor_id not in sensor_states:
        sensor_states[sensor_id] = {"state": "NORMAL", "timestamp": current_time}

    # Get the thresholds for the sensor
    thresholds = sensor_alarm_values.get(sensor_id, {"HIGH": 20, "LOW": 5})

    # Update the state based on the value
    if value >= thresholds["HIGH"]:
        sensor_states[sensor_id]["state"] = "HIGH"
        sensor_states[sensor_id]["timestamp"] = current_time
    elif value <= thresholds["LOW"]:
        sensor_states[sensor_id]["state"] = "LOW"
        sensor_states[sensor_id]["timestamp"] = current_time
    else:
        sensor_states[sensor_id]["state"] = "NORMAL"
        sensor_states[sensor_id]["timestamp"] = current_time

def check_alarms(sensor_id, value, current_time):
    """ Check if an alarm condition is met based on the sensor's state and duration """
    set_sensor_state(sensor_id, value, current_time)

    # Calculate the time the sensor has been in the current state
    last_timestamp = sensor_states[sensor_id]["timestamp"]
    duration = (current_time - last_timestamp).total_seconds()

    # If sensor is in "HIGH" or "LOW" state, check for alarm thresholds
    if sensor_states[sensor_id]["state"] != "NORMAL":
        if duration > THRESHOLD_X and not sensor_send_alarm.get(sensor_id, {}).get("send"):
            sensor_send_alarm[sensor_id] = {"send": 1, "alarm": sensor_states[sensor_id]["state"], "type": "X"}
            log_alarm(sensor_id, "X", current_time)

        if duration > THRESHOLD_Y and not sensor_send_alarm.get(sensor_id, {}).get("send"):
            sensor_send_alarm[sensor_id] = {"send": 1, "alarm": sensor_states[sensor_id]["state"], "type": "Y"}
            log_alarm(sensor_id, "Y", current_time)

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

        # Check for alarm conditions
        check_alarms(sensor_id, measurement, time)

        # Save the measurement in the database
        save_in_db(sensor_id, measurement, time)

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
