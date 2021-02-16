import redis
import datetime
import sys
import json
from flask import Flask, request

app = Flask(__name__)

r = redis.Redis(host='redis', port=6379, db=0)
channel = r.pubsub()
channel.subscribe("test-channel")


def sort_function(n):
    return datetime.datetime.fromtimestamp(float(n))


def get_start_index(datetime_keys, start_time):
    start_index = None
    for date_el in datetime_keys:
        if date_el >= start_time:
            start_index = datetime_keys.index(date_el)
            break
    return start_index


def get_end_index(datetime_keys, end_time):
    end_index = None
    for date_el in datetime_keys:
        if date_el >= end_time:
            end_index = datetime_keys.index(date_el)
            break
    return end_index


@app.route('/')
def hello_world():
    return 'Main Page'


@app.route('/publish', methods=('POST',))
def publish():
    message = request.json.get("content", None)
    if not message:
        return "{'error': 'You didn't set a content value'}", 400

    r.publish("test-channel", message)
    time = str(datetime.datetime.utcnow().timestamp())
    r.set(time, str(message))
    return "{'success': true}", 201


@app.route('/getLast')
def get_last():
    message = channel.get_message(True)
    if message:
        return "{'message': '" + message['data'].decode("utf-8") + "'}", 200
    else:
        return "{'error': 'You don`t have new messages'}"


@app.route('/getByTime')
def get_by_time():
    start_time = datetime.datetime.fromtimestamp(int(request.args.get("start", None)))
    end_time = datetime.datetime.fromtimestamp(int(request.args.get("end", None)))
    datetime_keys = list(map(sort_function, list(r.keys())))
    datetime_keys.sort()
    result = []

    start_index = get_start_index(datetime_keys, start_time)
    end_index = get_end_index(datetime_keys, end_time)

    if end_index:
        for date_el in datetime_keys[start_index:end_index]:
            result.append(r.get(str(date_el.timestamp())).decode("utf-8"))
    else:
        for date_el in datetime_keys[start_index:]:
            result.append(r.get(str(date_el.timestamp())).decode("utf-8"))
    return json.dumps(result), 200


if __name__ == '__main__':
    app.run(debug=True)
