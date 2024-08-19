import cv2
import mss
import numpy as np
from flask import Flask, Response
from multiprocessing import Process, Queue

app = Flask(__name__)

def process_capture(img_queue):
    with mss.mss() as sct:
        # Define screen region to capture
        monitor = sct.monitors[1]
        while True:
            # Capture the screen
            img = sct.grab(monitor)
            img_queue.put(img)

def generate_frames(img_queue, frame_queue):
    while True:
        img = img_queue.get()
        # Convert to numpy array
        img_np = np.array(img)
        # Convert it from BGRA to BGR for OpenCV
        frame = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
        # Encode the frame in JPEG format
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Put the frame in the frame queue
        frame_queue.put(frame)

def stream_frames(frame_queue):
    while True:
        frame = frame_queue.get()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def capture_screen_via_queue():
    img_queue = Queue()
    frame_queue = Queue()

    # Start the process to capture the screen
    p1 = Process(target=process_capture, args=(img_queue,))
    p1.start()

    # Start the process to generate frames
    p2 = Process(target=generate_frames, args=(img_queue, frame_queue))
    p2.start()

    while True:
        yield from stream_frames(frame_queue)

def capture_screen():
    with mss.mss() as sct:
        # Define screen region to capture
        monitor = sct.monitors[1]
        while True:
            # Capture the screen
            img = sct.grab(monitor)
            # Convert to numpy array
            img_np = np.array(img)
            # Convert it from BGRA to BGR for OpenCV
            frame = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
            # Encode the frame in JPEG format
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Yield the frame to stream it over HTTP
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/stream')
def stream():
    return Response(capture_screen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/health')
def healthy():
    return 'Healthy'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
