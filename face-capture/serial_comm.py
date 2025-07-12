import serial

class ESPSerial:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            print(f"[ESP32] Terhubung ke {port}")
            self.is_connected = True
        except Exception as e:
            print(f"[ESP32] Gagal terhubung: {e}")
            self.ser = None
            self.is_connected = False

    def send(self, message):
        if self.ser and self.ser.is_open:
            self.ser.write((message + '\n').encode())
            self.ser.flush()  # ⬅️ Tambahan penting!

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
