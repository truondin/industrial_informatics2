import sys
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
    def __init__(self):
        client = mqtt.Client()
        client.connect(BROKER_IP)
        self.client = client

    # event handler function
    def datachange_notification(self, node, val, data):
        print(node, round(val, AMOUNT_OF_DIGITS))
        sensor_id = 1
        value = 10

        self.client.publish("ii24/" + str(GROUP_ID) + "/sensor/" + str(sensor_id), value)


if __name__ == '__main__':
    # get node data from your server
    tempNode = client.get_node("ns=4;s=GVL.nMeasurement1")
    # handler
    handler = EventHandler()
    # subscription object
    sub = client.create_subscription(500, handler)
    # node
    handle = sub.subscribe_data_change(tempNode)
