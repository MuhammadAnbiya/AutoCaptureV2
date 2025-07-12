import cv2
import time
import os
import datetime
from threading import Thread
from queue import Queue
from serial_comm import ESPSerial
from gdrive_upload import setup_drive, upload_worker

# Path ke overlay PNG
overlay_path = "/media/muhammadanbiya/Data 1/AutoCapture+/frame.png"
overlay_img = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
if overlay_img is None:
    print(f"[ERROR] Gagal memuat gambar overlay: {overlay_path}. Pastikan path benar.")
    exit()

# Pisahkan alpha dan BGR jika ada channel alpha
if overlay_img.shape[2] == 4:
    overlay_alpha = overlay_img[:, :, 3] / 255.0
    overlay_bgr = overlay_img[:, :, :3]
else:
    overlay_alpha = None
    overlay_bgr = overlay_img

# Folder simpan foto
save_dir = "captured"
os.makedirs(save_dir, exist_ok=True)

# Kamera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)

# Load Haar Cascade
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# Inisialisasi Serial ESP32
esp = ESPSerial(port='/dev/ttyUSB0', baudrate=9600)

# Queue
upload_queue = Queue()
capture_queue = Queue()

# Google Drive
drive = setup_drive()
Thread(target=upload_worker, args=(upload_queue, drive), daemon=True).start()

# Worker Simpan + Upload
def capture_worker():
    while True:
        frame_to_save = capture_queue.get()
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"face_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)
        
        cv2.imwrite(filepath, frame_to_save)
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

# Start worker
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

    display_frame = frame.copy()

    # Tampilkan kotak pada wajah untuk preview (opsional)
    for (x, y, w, h) in faces:
        cv2.rectangle(display_frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

    # Jika wajah terdeteksi dan delay cukup, proses overlay dan simpan
    if len(faces) > 0 and time.time() - last_capture_time > capture_delay:
        print("[INFO] Wajah terdeteksi, memproses foto dengan overlay...")
        frame_with_overlay = frame.copy()

        # Resize overlay sesuai ukuran frame
        overlay_resized = cv2.resize(overlay_bgr, (frame.shape[1], frame.shape[0]))

        if overlay_alpha is not None:
            alpha_resized = cv2.resize(overlay_alpha, (frame.shape[1], frame.shape[0]))
            for c in range(3):
                frame_with_overlay[:, :, c] = (
                    frame_with_overlay[:, :, c] * (1 - alpha_resized) +
                    overlay_resized[:, :, c] * alpha_resized
                )
        else:
            frame_with_overlay = overlay_resized

        capture_queue.put(frame_with_overlay.copy())
        last_capture_time = time.time()

    cv2.imshow("Face Detection", display_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
