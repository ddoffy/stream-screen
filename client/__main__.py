import cv2
import socket
import numpy as np

# Set up socket connection
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 9999))

while True:
    # Receive the data
    data, _ = sock.recvfrom(65535)  # Adjust the buffer size as needed

    # Decode the JPEG image
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)

    # Display the image
    cv2.imshow('Stream', img)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
