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

# Capture queue
capture_queue = Queue()


# Function to handle save and upload
def capture_worker():
    while True:
        frame = capture_queue.get()
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"face_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)
        cv2.imwrite(filepath, frame)
        print(f"[INFO] Foto disimpan: {filepath}")
        upload_queue.put(filepath)
        capture_queue.task_done()


# Start worker thread
Thread(target=capture_worker, daemon=True).start()

print("[INFO] Mulai deteksi wajah... Tekan 'q' untuk keluar.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Gagal membaca frame.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) > 0 and time.time() - last_capture_time > capture_delay:
        print("[INFO] Wajah terdeteksi, memproses...")

        # Masukkan ke queue untuk diproses oleh thread
        capture_queue.put(frame.copy())

        if esp.is_connected:
            esp.send("FOTO_DISIMPAN")
        else:
            print("[ESP32] Serial tidak terhubung.")

        last_capture_time = time.time()

    cv2.imshow("Face Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
