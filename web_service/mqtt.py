from datetime import datetime

import paho.mqtt.client as mqtt
import db
import json

GROUP_ID = 420
BROKER_IP = "34.255.214.243"

THRESHOLD_X = 300  # 5 minutes
THRESHOLD_Y = 600  # 10 minutes
sensor_states = {}  # Format: {sensor_id: {"state": "HIGH/LOW/NORMAL", "timestamp": datetime}}
sensor_alarm_values = {} # Format: {sensor_id: {"HIGH": high_value, "LOW": low_value}}
sensor_send_alarm = {} # Format: {sensor_id: {"send": 0/1, "alarm": "HIGH/LOW", "type": "X/Y"}}
#sensor_alarm_values[0] = {"HIGH": 20, "LOW": 5}

def save_in_db(sensor_id, measurement, timestamp):
    print(f"sensor_id: {sensor_id} measurement: {str(measurement)}")
    if not db.sensor_exists(sensor_id):
        db.insert_sensor(sensor_id)
    db.insert_measurement(sensor_id, measurement, timestamp)
    

def set_sensor_state(sensor_id, value, current_time):
# checkuje stav sensoru, ktery je ulozeny v sensor_states dictionary.
# Pokud je stav jiny, nez aktualni(podle aktualne merene hodnoty senzoru), tak zmeni stav v sensor_states
# Je tam ukladan i aktualni cas, kdy se zmeni stav, takze pozdeji lze porovnanim s aktualnim casem (metoda check_alarms) zjistit dobu trvani stavu

    if sensor_states[sensor_id] == "NORMAL":
        if value >= sensor_alarm_values[sensor_id]["HIGH"]:
            sensor_states[sensor_id]["state"] = "HIGH"
            sensor_states[sensor_id]["timestamp"] = current_time
        if value <= sensor_alarm_values[sensor_id]["LOW"]:
            sensor_states[sensor_id]["state"] = "LOW"
            sensor_states[sensor_id]["timestamp"] = current_time
    elif sensor_states[sensor_id] == "HIGH":
        if value <= sensor_alarm_values[sensor_id]["LOW"]:
            sensor_states[sensor_id]["state"] = "LOW"
            sensor_states[sensor_id]["timestamp"] = current_time
        if sensor_alarm_values[sensor_id]["HIGH"] > value > sensor_alarm_values[sensor_id]["LOW"]:
            sensor_states[sensor_id]["state"] = "NORMAL"
            sensor_states[sensor_id]["timestamp"] = current_time
    elif sensor_states[sensor_id] == "LOW":
        if value >= sensor_alarm_values[sensor_id]["HIGH"]:
            sensor_states[sensor_id]["state"] = "HIGH"
            sensor_states[sensor_id]["timestamp"] = current_time
        if sensor_alarm_values[sensor_id]["HIGH"] > value > sensor_alarm_values[sensor_id]["LOW"]:
            sensor_states[sensor_id]["state"] = "NORMAL"
            sensor_states[sensor_id]["timestamp"] = current_time



def check_alarms(sensor_id, value, current_time):
    set_sensor_state(sensor_id, value, current_time)
    last_timestamp = sensor_states[sensor_id]["timestamp"]
    duration = (current_time - last_timestamp).total_seconds()
    if sensor_states[sensor_id]["state"] != "NORMAL":
        if duration > THRESHOLD_X:
            sensor_send_alarm[sensor_id] = {"send": 1, "alarm": f"{sensor_states[sensor_id]["state"]}", "type": "X"}
            #log_alarm(sensor_id, duration, THRESHOLD_X)
        if duration > THRESHOLD_Y:
            sensor_send_alarm[sensor_id] = {"send": 1, "alarm": f"{sensor_states[sensor_id]["state"]}", "type": "Y"}


#Mqtt on message
def on_message(client, userdata, msg):
    print("Got some Mqtt message ")
    sensor_id = msg.topic.split('/')[-1]
    payload = msg.payload.decode('utf-8')

    try:
        msg = json.loads(payload)
        print(msg)
        measurement = msg['value']
        timestamp = msg['timestamp']
        check_alarms(sensor_id, measurement, timestamp)
        format_string = "%Y-%m-%d %H:%M:%S"
        #if sensor_send_alarm[sensor_id]["send"] == 1:  TODO: send the alarm to database
            #send alarm to db
        time = datetime.strptime(timestamp, format_string)
        print(f"{time} {measurement}")
        save_in_db(sensor_id, measurement, time)
    except ValueError:
        print(f"Error: Invalid payload {payload} - expecting float")


#Mqtt thread
def start_subscription():
    print("Mqtt subscription started....")
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER_IP)
    client.subscribe("ii24/" + str(GROUP_ID) + "/sensor/#")  #subscribe all sensors

    try:
        rc = 0
        while rc == 0:
            rc = client.loop()
    finally:
        client.disconnect()
