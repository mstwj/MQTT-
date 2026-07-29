#include <Arduino.h>
#include "LCD_ST7567.h"

LCD_ST7567 lcd;
HardwareSerial Serial1(USART1);

#define SLAVE_ID 1
#define HOLDING_REG_COUNT 3  // Reg0: A相, Reg1: B相, Reg2: C相

// 保持寄存器，初始全切除 (0)
uint16_t holdingRegisters[HOLDING_REG_COUNT] = {0, 0, 0};

// ====== 最新硬件引脚定义 ======
// A 相
#define PIN_A_IN   PA4
#define PIN_A_CUT  PA5

// B 相
#define PIN_B_IN   PA6
#define PIN_B_CUT  PA7

// C 相
#define PIN_C_IN   PC4
#define PIN_C_CUT  PC5

// 脉冲保持时间：0.5秒 500ms)
#define PULSE_WIDTH_MS 500

uint8_t rxBuffer[64];
uint8_t rxIndex = 0;
unsigned long lastRxTime = 0;

// 标准 Modbus RTU CRC16 计算
uint16_t calculateCRC(uint8_t *buffer, uint8_t length) {
  uint16_t crc = 0xFFFF;
  for (int i = 0; i < length; i++) {
    crc ^= buffer[i];
    for (int j = 0; j < 8; j++) {
      if (crc & 0x0001) {
        crc = (crc >> 1) ^ 0xA001;
      } else {
        crc >>= 1;
      }
    }
  }
  return crc;
}

// 执行一相的投切脉冲（带互锁保护）
// is投: true 为“投”，false 为“切”
void executeSwitch(uint8_t pinIn, uint8_t pinCut, bool isIn) {
  // 强行确保两个引脚初始都是高电平（安全互锁）
  digitalWrite(pinIn, HIGH);
  digitalWrite(pinCut, HIGH);
  
  uint8_t targetPin = isIn ? pinIn : pinCut;
  
  // 发送 0.3s 的低电平脉冲
  digitalWrite(targetPin, LOW);
  delay(PULSE_WIDTH_MS);
  digitalWrite(targetPin, HIGH);
}

// 根据接收到的 Modbus 指令触发对应相
void processSingleSwitch(uint16_t regAddr, uint16_t regVal) {
  bool isOn = (regVal != 0);

  if (regAddr == 0) {       // A 相
    executeSwitch(PIN_A_IN, PIN_A_CUT, isOn);
  } 
  else if (regAddr == 1) { // B 相
    executeSwitch(PIN_B_IN, PIN_B_CUT, isOn);
  } 
  else if (regAddr == 2) { // C 相
    executeSwitch(PIN_C_IN, PIN_C_CUT, isOn);
  }
}

void setup() {
  lcd.Init();
  lcd.Clear();
  delay(100);

  lcd.ShowString(0, 0, "Indep Reg Control");

  // 初始化所有投切控制引脚为输出，且常态默认为高电平
  uint8_t pins[] = {PIN_A_IN, PIN_A_CUT, PIN_B_IN, PIN_B_CUT, PIN_C_IN, PIN_C_CUT};
  for (int i = 0; i < 6; i++) {
    pinMode(pins[i], OUTPUT);
    digitalWrite(pins[i], HIGH); // 常态高电平
  }

  // 初始化串口
  Serial1.setTx(PA9);
  Serial1.setRx(PA10);
  Serial1.begin(9600);
  delay(100);

  while (Serial1.available() > 0) Serial1.read();
}

void processModbusFrame(uint8_t *buf, uint8_t len) {
  if (len < 8 || buf[0] != SLAVE_ID) return;

  uint16_t recvCRC = buf[len - 2] | (buf[len - 1] << 8); 
  uint16_t calcCRC = calculateCRC(buf, len - 2);
  if (recvCRC != calcCRC) return;

  // 06 功能码：写单个寄存器
  if (buf[1] == 0x06) {
    uint16_t regAddr = (buf[2] << 8) | buf[3];
    uint16_t regVal  = (buf[4] << 8) | buf[5];

    if (regAddr < HOLDING_REG_COUNT) {
      holdingRegisters[regAddr] = regVal;   // 保存状态
      processSingleSwitch(regAddr, regVal); // 产生 0.3s 低电平脉冲
      
      Serial1.write(buf, len);               // 标准应答
    }
  }
  // 03 功能码：读保持寄存器
  else if (buf[1] == 0x03) {
    uint16_t startAddr = (buf[2] << 8) | buf[3];
    uint16_t regCount  = (buf[4] << 8) | buf[5];

    if ((startAddr + regCount) <= HOLDING_REG_COUNT) {
      uint8_t byteCount = regCount * 2;
      uint8_t respLen = 3 + byteCount + 2;
      uint8_t respBuf[16];

      respBuf[0] = SLAVE_ID;
      respBuf[1] = 0x03;
      respBuf[2] = byteCount;

      for (int i = 0; i < regCount; i++) {
        uint16_t val = holdingRegisters[startAddr + i];
        respBuf[3 + i * 2]     = val >> 8;
        respBuf[4 + i * 2]     = val & 0xFF;
      }

      uint16_t crc = calculateCRC(respBuf, 3 + byteCount);
      respBuf[3 + byteCount]     = crc & 0xFF;
      respBuf[3 + byteCount + 1] = crc >> 8;

      Serial1.write(respBuf, respLen);
    }
  }
}

void loop() {
  while (Serial1.available() > 0) {
    rxBuffer[rxIndex++] = Serial1.read();
    lastRxTime = millis();
    if (rxIndex >= 64) rxIndex = 0;
  }

  if (rxIndex > 0 && (millis() - lastRxTime > 30)) {
    processModbusFrame(rxBuffer, rxIndex);
    rxIndex = 0;
  }

  // 屏幕实时显示当前 A/B/C 三相的投切状态 (1=投, 0=切)
  static unsigned long lastUpdate = 0;
  if (millis() - lastUpdate > 200) {
    lastUpdate = millis();
    char buf[20];
    snprintf(buf, sizeof(buf), "A:%d  B:%d  C:%d", 
             holdingRegisters[0] ? 1 : 0, 
             holdingRegisters[1] ? 1 : 0, 
             holdingRegisters[2] ? 1 : 0);
    lcd.ShowString(0, 3, buf);
  }
}