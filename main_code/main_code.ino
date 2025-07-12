#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);  // Ganti 0x27 jika alamat I2C kamu berbeda

void setup() {
  Serial.begin(9600);
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Menunggu...");
}

void loop() {
  if (Serial.available()) {
    String pesan = Serial.readStringUntil('\n');
    pesan.trim();

    if (pesan == "FOTO_DISIMPAN") {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Foto Disimpan!");
      delay(3000);
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Menunggu...");
    }
  }
}
