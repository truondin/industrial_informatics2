from datetime import datetime

import paho.mqtt.client as mqtt
import db
import json

GROUP_ID = 420
BROKER_IP = "34.255.214.243"


def save_in_db(sensor_id, measurement, timestamp):
    print(f"sensor_id: {sensor_id} measurement: {str(measurement)}")
    if not db.sensor_exists(sensor_id):
        db.insert_sensor(sensor_id)
    db.insert_measurement(sensor_id, measurement, timestamp)


#Mqtt on message
def on_message(client, userdata, msg):
    print("Got some Mqtt message ")
    sensor_id = msg.topic.split('/')[-1]
    payload = msg.payload.decode('utf-8')

    try:
        msg = json.loads(payload)
        measurement = msg['measurement']
        timestamp = msg['timestamp']

        format_string = "%Y-%m-%d %H:%M:%S"
        time = datetime.strptime(timestamp, format_string)

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
