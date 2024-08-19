import cv2
import socket
import numpy as np
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind(('0.0.0.0', 9999))

CHUNK_SIZE = 9000  # Adjust the buffer
buffer = b''

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def udp_to_websocket():
    global buffer
    while True:
        # Receive UDP packets
        data, _ = udp_socket.recvfrom(CHUNK_SIZE)
        buffer += data

        try:
            # Attempt to decode the image
            img = cv2.imdecode(np.frombuffer(buffer, np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                # Encode image to JPEG and send over WebSocket
                _, jpeg_img = cv2.imencode('.jpg', img)
                socketio.emit('frame', jpeg_img.tobytes())
                buffer = b''  # Clear buffer after successful display
        except cv2.error:
            pass  # Continue receiving chunks

if __name__ == '__main__':
    socketio.start_background_task(target=udp_to_websocket)
    socketio.run(app, host='0.0.0.0', port=5000)
