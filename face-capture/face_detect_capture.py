import cv2
import time
import os
import datetime
from threading import Thread
from queue import Queue
from serial_comm import ESPSerial
from gdrive_upload import setup_drive, upload_worker

# Buat folder simpan foto
save_dir = "captured"
os.makedirs(save_dir, exist_ok=True)

# Kamera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)

# Load haarcascade
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# Inisialisasi Serial ESP32
esp = ESPSerial(port='/dev/ttyUSB0', baudrate=9600)

# Queue untuk upload & capture
upload_queue = Queue()
capture_queue = Queue()

# Google Drive
drive = setup_drive()
Thread(target=upload_worker, args=(upload_queue, drive), daemon=True).start()

# Worker simpan + upload
def capture_worker():
    while True:
        frame = capture_queue.get()
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"face_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)
        cv2.imwrite(filepath, frame)
        print(f"[INFO] Foto disimpan: {filepath}")
        upload_queue.put(filepath)

        try:
            if esp.is_connected:
                esp.send("FOTO_DISIMPAN")
                print("[ESP32] Pesan dikirim ke ESP32.")
            else:
                print("[ESP32] Tidak terhubung.")
        except Exception as e:
            print(f"[ERROR] Serial error: {e}")

        capture_queue.task_done()

# Start capture thread
Thread(target=capture_worker, daemon=True).start()

print("[INFO] Mulai deteksi wajah... Tekan 'q' untuk keluar.")

last_capture_time = 0
capture_delay = 3

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Tidak bisa membaca kamera.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) > 0 and time.time() - last_capture_time > capture_delay:
        print("[INFO] Wajah terdeteksi, memproses foto...")
        capture_queue.put(frame.copy())
        last_capture_time = time.time()

    cv2.imshow("Face Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
