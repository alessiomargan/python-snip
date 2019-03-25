#!/usr/bin/env python3
from threading import Lock
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit

import sys
sys.path.append('/home/amargan/work/code/python/python-snip')
from zmq_sub import ZMQ_sub, zmq_sub_option

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
zmq_thread = None
thread_lock = Lock()


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')



@app.route("/")
def hello():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('my_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('zmq_opt', namespace='/test')
def test_message(message):
    global zmq_thread
    print (message['data'])
    zmq_sub_args = message['data'].split()
    with thread_lock:
        if zmq_thread is not None:
            zmq_thread.stop()
            zmq_thread.join(0.5)
            zmq_thread = None
        opts = zmq_sub_option(zmq_sub_args)
        #zmq_thread = socketio.start_background_task(target=ZMQ_sub(**opts))
        zmq_thread = ZMQ_sub(**opts)
        zmq_thread.start()
    emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('ecat_cmd', namespace='/test')
def test_message(message):

    emit('my_response', {})


@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')


if __name__ == '__main__':
    socketio.run(app, debug=True)