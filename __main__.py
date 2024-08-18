import cv2
import mss
import numpy as np
from flask import Flask, Response

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
