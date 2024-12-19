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

    def create_mqtt_message(self, value):
        measurement = round(value, AMOUNT_OF_DIGITS)
        format_string = "%Y-%m-%d %H:%M:%S"
        timestamp = datetime.now()
        return {'value': measurement, 'timestamp': timestamp.strftime(format_string)}

    # event handler function
    def datachange_notification(self, node, val, data):
        print(node, round(val, AMOUNT_OF_DIGITS))

        value = self.create_mqtt_message(val)

        self.client.publish("ii24/" + str(GROUP_ID) + "/sensor/" + str(self.sensor_id), json.dumps(value))


if __name__ == '__main__':
    # Get node data from your server
    tempNode1 = client.get_node("ns=4;s=GVL.nMeasurement1")
    tempNode2 = client.get_node("ns=4;s=GVL.nMeasurement2")
    tempNode3 = client.get_node("ns=4;s=GVL.nMeasurement3")
    tempNode4 = client.get_node("ns=4;s=GVL.nMeasurement4")
    tempNode5 = client.get_node("ns=4;s=GVL.nMeasurement5")
    tempNode6 = client.get_node("ns=4;s=GVL.nMeasurement6")
    tempNode7 = client.get_node("ns=4;s=GVL.nMeasurement7")
    tempNode8 = client.get_node("ns=4;s=GVL.nMeasurement8")
    tempNode9 = client.get_node("ns=4;s=GVL.nMeasurement9")
    tempNode10 = client.get_node("ns=4;s=GVL.nMeasurement10")

    # Handlers
    handler1 = EventHandler(1)
    handler2 = EventHandler(2)
    handler3 = EventHandler(3)
    handler4 = EventHandler(4)
    handler5 = EventHandler(5)
    handler6 = EventHandler(6)
    handler7 = EventHandler(7)
    handler8 = EventHandler(8)
    handler9 = EventHandler(9)
    handler10 = EventHandler(10)

    # Subscription objects
    sub1 = client.create_subscription(500, handler1)
    sub2 = client.create_subscription(500, handler2)
    sub3 = client.create_subscription(500, handler3)
    sub4 = client.create_subscription(500, handler4)
    sub5 = client.create_subscription(500, handler5)
    sub6 = client.create_subscription(500, handler6)
    sub7 = client.create_subscription(500, handler7)
    sub8 = client.create_subscription(500, handler8)
    sub9 = client.create_subscription(500, handler9)
    sub10 = client.create_subscription(500, handler10)

    # Node handles
    handle1 = sub1.subscribe_data_change(tempNode1)
    handle2 = sub2.subscribe_data_change(tempNode2)
    handle3 = sub3.subscribe_data_change(tempNode3)
    handle4 = sub4.subscribe_data_change(tempNode4)
    handle5 = sub5.subscribe_data_change(tempNode5)
    handle6 = sub6.subscribe_data_change(tempNode6)
    handle7 = sub7.subscribe_data_change(tempNode7)
    handle8 = sub8.subscribe_data_change(tempNode8)
    handle9 = sub9.subscribe_data_change(tempNode9)
    handle10 = sub10.subscribe_data_change(tempNode10)
