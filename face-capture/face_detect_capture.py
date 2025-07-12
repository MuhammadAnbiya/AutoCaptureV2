import cv2
import time
import os
import datetime
from threading import Thread
from queue import Queue
from serial_comm import ESPSerial
from gdrive_upload import setup_drive, upload_worker

# Init folder
save_dir = "captured"
os.makedirs(save_dir, exist_ok=True)

# Init camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)

# Haar cascade
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# Serial
esp = ESPSerial(port='/dev/ttyUSB1', baudrate=9600)

# Upload queue & thread
upload_queue = Queue()
drive = setup_drive()
Thread(target=upload_worker, args=(upload_queue, drive), daemon=True).start()

# Timer
last_capture_time = 0
capture_delay = 3  # seconds

print("[INFO] Face detection started. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Failed to read frame.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) > 0 and time.time() - last_capture_time > capture_delay:
        print("[INFO] Wajah terdeteksi, tunggu 3 detik...")
        time.sleep(3)

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"face_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)
        cv2.imwrite(filepath, frame.copy())

        print(f"[INFO] Foto disimpan: {filepath}")
        upload_queue.put(filepath)

        if esp.is_connected:
            esp.send("FOTO_DISIMPAN")

        last_capture_time = time.time()

    cv2.imshow("Face Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
