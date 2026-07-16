#ifndef LCD_ST7567_H
#define LCD_ST7567_H

#include "Arduino.h"

// 硬件引脚定义，可外部修改
#define LCD_CS     PB12
#define LCD_SCLK   PB13
#define LCD_RS     PB14
#define LCD_MOSI   PB15
#define LCD_RES    PA6
#define LCD_BLK    PA7

// 电平操作宏
#define LCD_CS_Clr()    digitalWrite(LCD_CS, LOW)
#define LCD_CS_Set()    digitalWrite(LCD_CS, HIGH)
#define LCD_SCLK_Clr()  digitalWrite(LCD_SCLK, LOW)
#define LCD_SCLK_Set()  digitalWrite(LCD_SCLK, HIGH)
#define LCD_RS_Clr()    digitalWrite(LCD_RS, LOW)
#define LCD_RS_Set()    digitalWrite(LCD_RS, HIGH)
#define LCD_MOSI_Clr()  digitalWrite(LCD_MOSI, LOW)
#define LCD_MOSI_Set()  digitalWrite(LCD_MOSI, HIGH)
#define LCD_RES_Clr()   digitalWrite(LCD_RES, LOW)
#define LCD_RES_Set()   digitalWrite(LCD_RES, HIGH)
#define LCD_BLK_Set()   digitalWrite(LCD_BLK, HIGH)
#define LCD_BLK_Clr()   digitalWrite(LCD_BLK, LOW)

// 8*8 ASCII 数字+大写英文字库
extern uint8_t font8x8[][8];

class LCD_ST7567
{
public:
    // 初始化屏幕，复刻Keil完整时序
    void Init(void);

    // 清屏，全屏空白
    void Clear(void);

    // 设置显示坐标 x:0~127  y:0~7(页)
    void SetPos(uint8_t x, uint8_t y);

    // 显示单个字符（仅大写字母、数字）
    void ShowChar(uint8_t x, uint8_t y, char ch);

    // 显示字符串
    void ShowString(uint8_t x, uint8_t y, char *str);

private:
  uint8_t ReverseByte(uint8_t dat);
    // 底层SPI发送单字节
    void Writ_Bus(uint8_t dat);
    // 写显示数据
    void WR_DATA(uint8_t dat);
    // 写寄存器指令
    void WR_REG(uint8_t cmd);
};

#endif