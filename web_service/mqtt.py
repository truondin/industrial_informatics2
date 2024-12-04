import paho.mqtt.client as mqtt
import db

GROUP_ID = 420
BROKER_IP = "34.255.214.243"


def save_in_db(sensor_id, measurement):
    print(f"sensor_id: {sensor_id} measurement: {str(measurement)}")
    if not db.sensor_exists(sensor_id):
        db.insert_sensor(sensor_id)
    db.insert_measurement(sensor_id, measurement)


#Mqtt on message
def on_message(client, userdata, msg):
    print("Got some Mqtt message ")
    sensor_id = msg.topic.split('/')[-1]
    payload = msg.payload.decode('utf-8')

    try:
        measurement = float(payload)
        save_in_db(sensor_id, measurement)
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
