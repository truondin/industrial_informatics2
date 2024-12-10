import random

from flask import Flask, render_template, request
from datetime import datetime

import threading
import mqtt as mqtt_handler
import db
import json

from web_service.objects import State

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
        return db.get_measurements_until(to_date)
    elif to_date is None:
        return db.get_measurements_from(from_date)
    else:
        return db.get_measurements_in_time_range(from_date, to_date)


@app.route('/sensors/<sensor_id>/measurements/byTime', methods=['POST'])
def get_measurements_by_time_and_sensor_id(sensor_id):
    request_data = request.get_json()
    try:
        sensor_id = int(sensor_id)
        from_date = request_data['from']
        to_date = request_data['to']
        print(f"{sensor_id} {from_date} {to_date}")

        if from_date is None:
            return db.get_measurements_of_sensor_until(sensor_id, to_date)
        elif to_date is None:
            return db.get_measurements_of_sensor_from(sensor_id, from_date)
        else:
            return db.get_measurements_of_sensor_in_time_range(sensor_id, from_date, to_date)
    except ValueError:
        return "Invalid sensor id"

@app.route('/sensors/<sensor_id>/kpi', methods=['POST'])
def get_kpi_of_sensor(sensor_id):
    request_data = request.get_json()
    try:
        sensor_id = int(sensor_id)
        from_date = request_data['from']
        to_date = request_data['to']

        total = db.count_measurements_of_sensor_in_time_range(sensor_id, from_date, to_date)
        low = db.count_measurements_of_sensor_in_time_range(sensor_id, from_date, to_date, state=State.LOW)
        high = db.count_measurements_of_sensor_in_time_range(sensor_id, from_date, to_date, state=State.HIGH)
        normal = db.count_measurements_of_sensor_in_time_range(sensor_id, from_date, to_date, state=State.NORMAL)

        low_percentage = (low / total) * 100 if total else 0
        normal_percentage = (normal / total) * 100 if total else 0
        high_percentage = (high / total) * 100 if total else 0

        return {"low": low_percentage, "normal": normal_percentage, "high": high_percentage}

    except ValueError:
        return "Invalid sensor id"

@app.route('/alarms/<sensor_id>', methods=['GET'])
def get_alarms_by_sensor_id(sensor_id):
    try:
        sensor_id = int(sensor_id)
        alarms = db.get_alarms_by_sensor_id(sensor_id)
        return {"alarms": alarms}
    except ValueError:
        return {"error": "Invalid sensor ID"}, 400

@app.route('/alarms/<sensor_id>/byTime', methods=['POST'])
def get_alarms_by_sensor_and_time(sensor_id):
    try:
        sensor_id = int(sensor_id)
        request_data = request.get_json()
        from_date = request_data.get('from')
        to_date = request_data.get('to')
        alarms = db.get_alarms_in_time_range(sensor_id, from_date, to_date)
        print(f"{sensor_id} {from_date} {to_date} {alarms}")

        if not from_date or not to_date:
            return {"error": "Both 'from' and 'to' timestamps are required."}, 400
        return {"alarms": alarms}
    except ValueError:
        return {"error": "Invalid sensor ID"}, 400
    except Exception as e:
        return {"error": str(e)}, 500


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

    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    robot_data = []
    for i in range(10):
        currentState = random.choice(possibleStates)
        value = random.randint(0, 100)
        robot_data.append({"currentState": currentState, "lastTimeConnected": current_time, "value": value})
    return json.dumps(robot_data)



if __name__ == '__main__':
    startThreads()
    db.create_db()
    app.run()