import mss
import cv2
import socket
import numpy as np

# Screen capture dimensions
width, height = 1920, 1080  # Adjust based on your screen resolution

# Set up socket connection
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('<RECEIVER_IP>', 9999)

with mss.mss() as sct:
    monitor = {"top": 0, "left": 0, "width": width, "height": height}

    while True:
        # Capture the screen
        img = np.array(sct.grab(monitor))

        # Convert the image to JPEG to reduce size
        _, jpeg_img = cv2.imencode('.jpg', img)

        # Send the JPEG-encoded image over the socket
        sock.sendto(jpeg_img.tobytes(), server_address)
