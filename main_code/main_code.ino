#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Ganti ke 0x3F jika 0x27 tidak muncul
LiquidCrystal_I2C lcd(0x27, 20, 4);  // 20 karakter, 4 baris

void setup() {
  Wire.begin(21, 22);               // SDA = 21, SCL = 22 (ESP32 default)
  lcd.init();
  lcd.backlight();
  
  lcd.setCursor(0, 0);
  lcd.print("Status: Menunggu");
  Serial.begin(115200);
}

void loop() {
  if (Serial.available()) {
    String msg = Serial.readStringUntil('\n');  // baca hingga newline

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Status:");
    
    // Cetak max 3 baris setelah "Status:"
    int line = 1;
    while (msg.length() > 0 && line <= 3) {
      int newlineIndex = msg.indexOf('\n');
      String lineMsg;

      if (newlineIndex != -1) {
        lineMsg = msg.substring(0, newlineIndex);
        msg = msg.substring(newlineIndex + 1);
      } else {
        lineMsg = msg;
        msg = "";
      }

      lcd.setCursor(0, line++);
      lcd.print(lineMsg);
    }

    Serial.println("[LCD] Pesan diterima & ditampilkan");
  }
}
