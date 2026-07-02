// USART1：RX=PA10，TX=PA9
HardwareSerial Serial1(PA10, PA9);

void setup() {
  Serial1.begin(115200);
  // 加长延时，避免ST-LINK调试上电打印丢失
  delay(1000);
  Serial1.println("USART1 Test | TX:PA9  RX:PA10");
  Serial1.flush(); // 强制刷完缓冲区，防止丢字
}

void loop() {
  Serial1.println("Loop running...");
  delay(1000);
}