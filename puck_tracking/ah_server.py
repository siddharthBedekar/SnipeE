import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit

msg ='x1y1'

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def hello(name=None):
    return render_template('game.html')

@socketio.on('message')
def handle_message(data):
    print('received message: ' + str(data))
    emit('updatePuck', msg)

if __name__ == '__main__':
    socketio.run(app)
    threading.Thread(target=app.run).start()