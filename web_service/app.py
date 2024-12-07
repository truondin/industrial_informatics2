import random

from flask import Flask, render_template, request
from datetime import datetime

import threading
import mqtt as mqtt_handler
import db
import json


app = Flask(__name__)
threadStarted=False


@app.route('/hello', methods=['GET'])
def helloWorld():
    print("Hello world endpoint")
    return "Hello World"


@app.route('/sensors/<sensor_id>/measurements', methods=['GET'])
def get_measurements_by_sensor_id(sensor_id):
    try:
        sensor_id = int(sensor_id)
        return db.get_measurements_by_sensor_id(sensor_id)
    except ValueError:
        return "Invalid sensor id"


@app.route('/sensors/all/measurements', methods=['GET'])
def get_all_measurements():
    return db.get_all_measurements()


@app.route('/sensors/all/measurements/byTime', methods=['GET'])
def get_measurements_by_time():
    request_data = request.get_json()
    from_date = request_data['from']
    to_date = request_data['to']
    if from_date is None:
        db.get_measurements_until(to_date)
    elif to_date is None:
        db.get_measurements_from(from_date)
    else:
        return db.get_measurements_in_time_range(from_date, to_date)


def startThreads():
    print("Start threads attempt")
    global threadStarted
    if (threadStarted):
        return "Threads have started already"
    else:
        threadStarted=True
        #Mqtt
        x = threading.Thread(target=mqtt_handler.start_subscription)
        x.start()

        return "Starting threads"



@app.route('/<string:page_name>/')
def static_page(page_name):
    nID = request.args.get('nID')
    return render_template('%s.html' % page_name,nID=nID)


@app.route('/robots/<rID>/latest', methods=['GET'])
def getRobotLatestState(rID):
    possibleStates = ["ACTIVE", "IDLE", "DOWN"]
    currentState = random.choice(possibleStates)

    now = datetime.now()


    current_time = now.strftime("%H:%M:%S")
    return json.dumps({"currentState": currentState, "lastTimeConnected": current_time})



if __name__ == '__main__':
    try:
        startThreads()
        db.create_db()
        app.run()
    finally:
        print("Stopping web service")