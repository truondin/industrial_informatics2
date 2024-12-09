from paho.mqtt import client as mqtt
from paho.mqtt import publish as publish
import random
from datetime import datetime as datetime
from flask import Flask, render_template, request
import threading


app = Flask(__name__)

broker = '34.255.214.243'
#port = 1883        # NO PORT
groupId = 420
client = None

def getTopic(sensorId):
    return f"ii24/{groupId}/sensors/{sensorId}/measurements"


def connectMQTT():
    print("Connecting to MQTT server...")
    client = mqtt.Client()
    print(client.connect(broker))


#@app.route('/mqtt/publish/<sensor_id>', methods=['POST'])
def mqtt_publish_message(sensor_id):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sens1_meas = f"{now};{random.randint(1, 10)}"
    client.publish(getTopic(sensor_id), sens1_meas)

if __name__ == '__main__':
    connectMQTT()

    #app.run(debug=True)

    client.loop_start()

    while True:
        mqtt_publish_message(1)

    client.loop_stop()