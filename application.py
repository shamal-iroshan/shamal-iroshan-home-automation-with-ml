from flask import Flask,render_template,request, make_response, redirect
from flask import jsonify
from flask_pymongo import PyMongo
from flask_pymongo import ObjectId
from flask_cors import CORS, cross_origin
from flask_mqtt import Mqtt
from flask_awscognito import AWSCognitoAuthentication
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime


application = Flask(__name__)
application.config["MONGO_URI"] = ""
mongodb_client = PyMongo(application)
db = mongodb_client.db
cors = CORS(application)
application.secret_key = "my super secret key"
application.config['CORS_HEADERS'] = 'Content-Type'
application.config['MQTT_BROKER_URL'] = 'test.mosquitto.org'
application.config['MQTT_BROKER_PORT'] = 1883
application.config['MQTT_USERNAME'] = ''
application.config['MQTT_PASSWORD'] = ''
application.config['MQTT_REFRESH_TIME'] = 1.0
application.config['MQTT_KEEPALIVE'] = 5
application.config['MQTT_TLS_ENABLED'] = False

application.config['AWS_COGNITO_DOMAIN'] = ""
application.config['AWS_DEFAULT_REGION'] = ""
application.config['AWS_COGNITO_USER_POOL_ID'] = ""
application.config['AWS_COGNITO_USER_POOL_CLIENT_ID'] = ""
application.config['AWS_COGNITO_USER_POOL_CLIENT_SECRET'] = ""
application.config['AWS_COGNITO_REDIRECT_URL'] = ""
mqtt = Mqtt(application)
aws_auth = AWSCognitoAuthentication(application)

# sheduler
def handle_switching():
    days = [1, 2, 3, 4, 5, 6, 0]
    data = db.history.find_one({"day": days[datetime.today().weekday()]})
    if ((datetime.today().strftime("%I:%M:%S %p") > data['on']) and (datetime.today().strftime("%I:%M:%S %p") < data['off'])): 
        mqtt.publish(f"QvnA%FZ*9P/automated", 1)
    else: 
        mqtt.publish(f"QvnA%FZ*9P/automated", 0)

scheduler = BackgroundScheduler()
scheduler.add_job(func=handle_switching, trigger="interval", seconds=60)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# @application.route('/home', methods=["GET"])
# def route_home():
#     if request.args:
#         try:
#             access_token = aws_auth.get_access_token(request.args)
#             if access_token:
#                 return render_template('index.html')
#             else: 
#                 return "Error"
#         except:
#             return "Error"

#     else:
#         return "Error"

@application.route('/')
def sign_in():
    return render_template('index.html')

# @application.route('/aws_cognito_redirect')
# def aws_cognito_redirect():
#     access_token = aws_auth.get_access_token(request.args)
#     return jsonify({'access_token': access_token})

# @application.route('/a')
# @aws_auth.authentication_required
# def index():
#     claims = aws_auth.claims # or g.cognito_claims
#     return jsonify({'claims': claims})

# ========================================================

@application.route('/login', methods=["POST"])
@cross_origin()
def route_login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        json = {"username": username, "password": password}
    return make_response(jsonify(json), 200)

@application.route('/get-config', methods=['GET'])
@cross_origin()
def route_get_config():
    if request.method == "GET":
        data = db.config.find()
        response = []
        for document in data:
            document['_id'] = str(document['_id'])
            response.append(document)
        return make_response(jsonify(response), 200)

@application.route('/get-status', methods=["GET"])
@cross_origin()
def route_get_status():
    if request.method == "GET":
        data = db.devices.find()
        response = []
        for document in data:
            document['_id'] = str(document['_id'])
            response.append(document)
        return make_response(jsonify(response), 200)

@application.route('/update-state', methods=['PATCH'])
@cross_origin()
def route_update_state():
    if request.method == "PATCH":
        deviceId = request.args.get('deviceId')
        state = request.args.get('state')
        name = request.args.get('name')
        day = request.args.get('day')
        on = request.args.get('on')
        off = request.args.get('off')
        mqtt.publish(f"QvnA%FZ*9P/{name}", state)
        db.devices.update_one({"_id":ObjectId(deviceId)},{"$set":{"state":int(state)}})
        if name == "automated":
            if on:
                db.history.update_one({"day":int(day)}, {"$set":{"on":on}})
            elif off:
                db.history.update_one({"day":int(day)}, {"$set":{"off":off}})
    return make_response("updated the device state")

@application.route('/add-device', methods=["POST"])
@cross_origin()
def route_add_device():
    if request.method == "POST":
        deviceName = request.args.get('deviceName')
        db.devices.insert_one({"device": deviceName, "state": 0})
    return make_response("device added", 201)

@application.route('/delete-device', methods=["DELETE"])
@cross_origin()
def route_delete_device():
    if request.method == "DELETE":
        deviceId = request.args.get('deviceId')
        db.devices.delete_one({ "_id": ObjectId(deviceId)})
    return make_response("device deleted", 200)

@application.route('/edit-device', methods=["PATCH"])
@cross_origin()
def route_edit_device():
    if request.method == "PATCH":
        deviceId = request.args.get('deviceId')
        deviceName = request.args.get('deviceName')
        db.devices.update_one({"_id":ObjectId(deviceId)},{"$set":{"device":deviceName}})
    return make_response("device updated", 200)

# =================================================================================


if __name__ == '__main__':
    application.run(debug=False)