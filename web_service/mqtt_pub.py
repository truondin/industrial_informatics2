from paho.mqtt import client as mqtt
from datetime import datetime as datetime
import json
from opcua import Client
import time

broker = '34.255.214.243'
#port = 1883        # NO PORT
groupId = 420
client = None

def get_topic(sensorId):
    return f"ii24/{groupId}/sensors/{sensorId}/measurements"


def connect_mqtt():
    global client
    print("Connecting to MQTT server...")
    client = mqtt.Client()
    client.connect(broker)
    client.loop_start()


def mqtt_publish_message(sensor_id, measurement, timestamp):
    topic = get_topic(sensor_id)
    payload = {
        "value": measurement,
        "timestamp": timestamp
    }
    client.publish(topic, json.dumps(payload))
    print(f"Published to {topic}: {payload}")


if __name__ == '__main__':
    connect_mqtt()
