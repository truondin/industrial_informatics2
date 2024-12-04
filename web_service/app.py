
from flask import Flask, render_template, request

import threading
import mqtt as mqtt_handler
import db


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


if __name__ == '__main__':
    startThreads()
    db.create_db()
    app.run()