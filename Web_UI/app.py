#Import requests from flask
import random
import json
from flask import Flask, render_template,request
from datetime import datetime

app = Flask(__name__)


#Serve dynamic pages

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
        app.run()
    finally:
        print("jaj")