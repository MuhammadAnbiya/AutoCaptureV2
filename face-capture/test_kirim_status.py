from serial_comm import ESPSerial
import time

esp = ESPSerial(port="/dev/ttyUSB0")

status_list = [
    "Wajah Terdeteksi",
    "Foto Disimpan",
    "Foto Diunggah"
]

for status in status_list:
    esp.send(status)
    time.sleep(3)

esp.send("Selesai")
esp.close()
