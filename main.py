import sys
import json
from datetime import datetime

import paho.mqtt.client as mqtt

from opcua import Client


GROUP_ID = 420
BROKER_IP = "34.255.214.243"


'''
    OPC UA client with subscription method
    instead of polling method
'''
AMOUNT_OF_DIGITS = 2

# OPC UA server end point
url = "opc.tcp://localhost:4840"

# Connecting to the server
try:
    client = Client(url)
    client.connect()
    print("Connected to OPC UA Server")
except Exception as err:
    print("server not found")
    sys.exit(1)


class EventHandler(object):
    def __init__(self, sensor_id):
        client = mqtt.Client()
        client.connect(BROKER_IP)
        self.client = client
        self.sensor_id = sensor_id

    # event handler function
    def datachange_notification(self, node, val, data):
        print(node, round(val, AMOUNT_OF_DIGITS))

        measurement = round(val, AMOUNT_OF_DIGITS)
        format_string = "%Y-%m-%d %H:%M:%S"
        timestamp = datetime.now()
        value = {'value': measurement, 'timestamp': timestamp.strftime(format_string)}

        self.client.publish("ii24/" + str(GROUP_ID) + "/sensor/" + str(self.sensor_id), json.dumps(value))


if __name__ == '__main__':
    # get node data from your server
    tempNode = client.get_node("ns=4;s=GVL.nMeasurement1")
    tempNode2 = client.get_node("ns=4;s=GVL.nMeasurement2")
    # handler
    handler = EventHandler(1)
    handler2 = EventHandler(2)
    # subscription object
    sub = client.create_subscription(500, handler)
    sub2 = client.create_subscription(500, handler2)
    # node
    handle = sub.subscribe_data_change(tempNode)
    handle2 = sub2.subscribe_data_change(tempNode2)
