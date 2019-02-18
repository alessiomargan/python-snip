#!/usr/bin/env python3
from threading import Lock
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
import json
import sys
sys.path.append('/home/amargan/work/code/python/python-snip')
from zmq_sub import ZMQ_sub, zmq_sub_option, cb_map

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = "threading"  # None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread_lock = Lock()
zmq_thread = None
tmp_cb = None


@app.route("/")
def hello():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')


@socketio.on('zmq_opt', namespace='/test')
def test_message(message):
    global zmq_thread
    global tmp_cb
    print(message['data'])
    zmq_sub_args = message['data'].split()
    with thread_lock:
        if zmq_thread is not None:
            zmq_thread.stop()
            zmq_thread.join(0.5)
            zmq_thread = None
        opts = zmq_sub_option(zmq_sub_args)
        tmp_cb = cb_map['protobuf_cb']
        cb_map['flask_cb'] = zmq_cb
        opts['cb'] = 'flask_cb'
        zmq_thread = ZMQ_sub(**opts)
        zmq_thread.start()
    emit('my_response', {'data': 'Thread running ...', 'count': 0})


def zmq_cb(msg_id, data, signals):
    global tmp_cb
    z_id, z_data = tmp_cb(msg_id, data, signals)
    socketio.emit('zdata', {'z_id': z_id, 'z_data': z_data},
                  namespace='/test')


if __name__ == '__main__':
    socketio.run(app, debug=True)
