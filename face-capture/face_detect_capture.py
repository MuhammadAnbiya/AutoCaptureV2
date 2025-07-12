import cv2
import time
import os
import datetime
from threading import Thread
from queue import Queue
from serial_comm import ESPSerial
from gdrive_upload import setup_drive, upload_worker

# --- NEW: Load the overlay PNG image ---
# Make sure the path to your PNG is correct
overlay_path = "/media/muhammadanbiya/Data 1/AutoCapture+/frame.png"
overlay_img = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED) # IMREAD_UNCHANGED to get alpha channel
if overlay_img is None:
    print(f"[ERROR] Gagal memuat gambar overlay: {overlay_path}. Pastikan path benar.")
    exit()

# If the overlay has an alpha channel (transparency), separate it
if overlay_img.shape[2] == 4:
    overlay_alpha = overlay_img[:, :, 3] / 255.0
    overlay_bgr = overlay_img[:, :, :3]
else:
    overlay_alpha = None # No alpha channel, treat as opaque
    overlay_bgr = overlay_img
# --- END NEW ---

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
        frame_to_save = capture_queue.get() # Get the frame that already has the overlay
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"face_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)
        
        # Save the frame with the overlay
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

    # Create a copy of the frame to draw on, so the original 'frame' for display isn't affected
    display_frame = frame.copy() 
    frame_with_overlay = frame.copy() # This will be the frame sent to the queue

    if len(faces) > 0:
        for (x, y, w, h) in faces:
            # Draw rectangle on the display frame
            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

            # --- NEW: Overlay the PNG onto the frame_with_overlay ---
            # Resize overlay image to fit the face
            overlay_resized = cv2.resize(overlay_bgr, (w, h))
            
            # Get the region of interest (ROI) where the overlay will be placed
            roi = frame_with_overlay[y:y+h, x:x+w]

            # If the overlay has an alpha channel, use it for blending
            if overlay_alpha is not None:
                alpha_resized = cv2.resize(overlay_alpha, (w, h))
                for c in range(0, 3):
                    frame_with_overlay[y:y+h, x:x+w, c] = (roi[:, :, c] * (1 - alpha_resized) +
                                                         overlay_resized[:, :, c] * alpha_resized)
            else:
                # If no alpha channel, just copy the overlay directly
                frame_with_overlay[y:y+h, x:x+w] = overlay_resized
            # --- END NEW ---

        # Only put the frame into the queue if a face is detected and delay has passed
        if time.time() - last_capture_time > capture_delay:
            print("[INFO] Wajah terdeteksi, memproses foto dengan overlay...")
            capture_queue.put(frame_with_overlay.copy()) # Put the frame with overlay
            last_capture_time = time.time()

    cv2.imshow("Face Detection", display_frame) # Show the frame with face rectangles
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()