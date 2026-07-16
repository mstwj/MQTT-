#include "LCD_ST7567.h"

LCD_ST7567 lcd;

void setup()
{
  lcd.Init();
  lcd.Clear();
  delay(100);
  lcd.ShowString(0,0,"TEST 1233333 ABC");
  lcd.ShowString(0,2,"STM32 ST7567");
  lcd.ShowString(0,4,"ARDUINO LIBRARY");
}

void loop()
{

}