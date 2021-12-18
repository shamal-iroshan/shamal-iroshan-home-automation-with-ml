from flask import Flask,render_template,request, make_response
from flask import jsonify
from flask_pymongo import PyMongo
from flask_pymongo import ObjectId
from flask_cors import CORS, cross_origin
from flask_mqtt import Mqtt

application = Flask(__name__)
application.config["MONGO_URI"] = "mongodb+srv://shamal:CUzcTxAqUVRW8Xan@cluster0.4brhm.mongodb.net/ijse_final?authSource=admin&replicaSet=atlas-zn6p9b-shard-0&w=majority&readPreference=primary&appname=MongoDB%20Compass&retryWrites=true&ssl=true"
mongodb_client = PyMongo(application)
db = mongodb_client.db
cors = CORS(application)
application.config['CORS_HEADERS'] = 'Content-Type'
application.config['MQTT_BROKER_URL'] = 'test.mosquitto.org'
application.config['MQTT_BROKER_PORT'] = 1883
application.config['MQTT_USERNAME'] = ''
application.config['MQTT_PASSWORD'] = ''
application.config['MQTT_REFRESH_TIME'] = 1.0
application.config['MQTT_KEEPALIVE'] = 5
application.config['MQTT_TLS_ENABLED'] = False
mqtt = Mqtt(application)

@application.route('/', methods=["GET"])
def route_home():
    return render_template('index.html')

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
        mqtt.publish(f"QvnA%FZ*9P/{name}", state)
        db.devices.update_one({"_id":ObjectId(deviceId)},{"$set":{"state":int(state)}})
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

# @mqtt.on_connect()
# def handle_connect(client, userdata, flags, rc):
#     mqtt.subscribe('home/mytopic')

# @mqtt.on_message()
# def handle_mqtt_message(client, userdata, message):
#     data = dict(
#         topic=message.topic,
#         payload=message.payload.decode()
#     )
#     print(data)

# @application.route('/mqtt-publish', methods=["POST"])
# @cross_origin()
# def route_mqtt_publish():
#     if request.method == "POST":
#         mqtt.publish('home/mytopic', 'this is my message')
#     return make_response("published", 200)

if __name__ == '__main__':
    application.run(debug=True)