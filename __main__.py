import cv2
import mss
import numpy as np
from flask import Flask, Response
from multiprocessing import Process, Queue, Pipe, process
import time
import sounddevice as sd

app = Flask(__name__)


# Audio configuration
CHANNELS = 2
RATE = 44100
CHUNK = 1024
DEVICE = 3

def capturing_audio(conn):
    with sd.InputStream(channels=CHANNELS, samplerate=RATE, blocksize=CHUNK, dtype='int16', device=DEVICE) as stream:
        while True:
            data = stream.read(CHUNK)[0]
            conn.send(data)

def wav_header():
    import struct
    fmt = '<4sI4s4sIHHIIHH4sI'
    chunk_size = 36 + 8 * CHUNK
    subchunk2_size = CHUNK * 2
    return struct.pack(fmt,
                       b'RIFF', chunk_size, b'WAVE',
                       b'fmt ', 16, 1, CHANNELS, RATE, RATE * CHANNELS * 2,
                       CHANNELS * 2, 16, b'data', subchunk2_size)

def generate_audio():
    device_info = sd.query_devices(DEVICE, 'input')
    supported_channels = device_info['max_input_channels']

    CHANNELS = min(supported_channels, 2)  # Use the maximum supported, up to stereo
    with sd.InputStream(channels=CHANNELS, samplerate=RATE, blocksize=CHUNK, dtype='int16', device=DEVICE) as stream:
        while True:
            data = stream.read(CHUNK)[0]
            # yield audio data over HTTP
            # with WAV header (simplified for streaming)
            # content type: audio/wav
            yield wav_header() + data.tobytes() + b'\r\n'

def capturing(conn, fps=30):
    with mss.mss() as sct:
        # Define screen region to capture
        monitor = sct.monitors[1]
        while True:
            # Capture the screen
            img = sct.grab(monitor)
            time.sleep(1/fps)
            conn.send(img)

def convertToArray(conn, child_conn):
    while True:
        img = conn.recv()
        # Convert to numpy array
        img_np = np.array(img)
        child_conn.send(img_np)

def convertToBGR(conn, child_conn):
    while True:
        img_np = conn.recv()
        # Convert it from BGRA to BGR for OpenCV
        frame = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
        child_conn.send(frame)

def convertToJPEG(conn, child_conn):
    while True:
        img = conn.recv()
        # Encode the frame in JPEG format
        _, buffer = cv2.imencode('.jpg', img)
        child_conn.send(buffer)

def convertToBytes(conn, child_conn):
    while True:
        img = conn.recv()
        # Convert to bytes
        img_bytes = img.tobytes()
        child_conn.send(img_bytes)

def capture_screen_via_pipe():
    parent_conn, child_conn = Pipe()

    # Start the process to capture the screen
    p1 = Process(target=capturing, args=(child_conn,60))
    p1.start()

    # Start the process to convert to numpy array
    parrent_convert_to_array_conn, child_convert_to_array_conn = Pipe()
    p2 = Process(target=convertToArray, args=(parent_conn, child_convert_to_array_conn))
    p2.start()


    # Start the process to convert to BGR
    parrent_convert_to_bgr_conn, child_convert_to_bgr_conn = Pipe()
    p3 = Process(target=convertToBGR, args=(parrent_convert_to_array_conn, child_convert_to_bgr_conn))
    p3.start()

    # Start the process to convert to JPEG
    parrent_convert_to_jpeg_conn, child_convert_to_jpeg_conn = Pipe()
    p4 = Process(target=convertToJPEG, args=(parrent_convert_to_bgr_conn, child_convert_to_jpeg_conn))
    p4.start()

    # Start the process to convert to bytes
    parrent_convert_to_bytes_conn, child_convert_to_bytes_conn = Pipe()
    p5 = Process(target=convertToBytes, args=(parrent_convert_to_jpeg_conn, child_convert_to_bytes_conn))
    p5.start()

    while True:
        frame = parrent_convert_to_bytes_conn.recv()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    # while True:
    #     img = parent_conn.recv()
    #     # Convert to numpy array
    #     img_np = np.array(img)
    #     # Convert it from BGRA to BGR for OpenCV
    #     frame = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
    #     # Encode the frame in JPEG format
    #     _, buffer = cv2.imencode('.jpg', frame)
    #     frame = buffer.tobytes()
    #     yield (b'--frame\r\n'
    #            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


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
    return Response(capture_screen_via_pipe(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/audio')
def audio():
    # parent_conn, child_conn = Pipe()

    # # Start the process to capture the audio
    # p1 = Process(target=capturing_audio, args=(child_conn,))
    # p1.start()

    # WAV header (simplified for streaming)
    return Response(generate_audio(),
                    mimetype='audio/wav')


@app.route('/health')
def healthy():
    return 'Healthy'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
