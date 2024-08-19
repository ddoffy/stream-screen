import mss
import cv2
import socket
import numpy as np

# Screen capture dimensions
width, height = 1920, 1080  # Adjust based on your screen resolution

# Set up socket connection
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('127.0.0.1', 9999)
CHUNK_SIZE = 9000  # Adjust the buffer

with mss.mss() as sct:
    monitor = {"top": 0, "left": 0, "width": width, "height": height}

    while True:
        # Capture the screen
        img = np.array(sct.grab(monitor))

        # Convert the image to JPEG to reduce size
        _, jpeg_img = cv2.imencode('.jpg', img)

        img_bytes = jpeg_img.tobytes()

        img_length = len(img_bytes)
        # Send the image in CHUNK_SIZE img_bytes over the socket
        for i in range(0, img_length, CHUNK_SIZE):
            print('send chunk', i)
            chunk = img_bytes[i:i + CHUNK_SIZE]
            sock.sendto(chunk, server_address)

        # Send the JPEG-encoded image over the socket
        # sock.sendto(jpeg_img.tobytes(), server_address)
