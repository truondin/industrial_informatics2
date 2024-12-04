
from flask import Flask, render_template,request

import threading
import mqtt as mqtt_handler
import db


app = Flask(__name__)
threadStarted=False


@app.route('/hello', methods=['GET'])
def helloWorld():
    print("Hello world endpoint")
    return "Hello World"


@app.route('/start', methods=['GET'])
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