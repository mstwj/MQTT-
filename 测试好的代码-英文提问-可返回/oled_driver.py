# oled_driver.py
from machine import Pin, I2C,SoftI2C
import ssd1306
from font_hzk16 import HZK16Font  # 引入字库解析模块

SDA_PIN = 47
SCL_PIN = 21

i2c = SoftI2C(sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)

oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# 2. 初始化字库对象 (确保 HZK16 文件已上传至根目录)
font = HZK16Font("/HZK16")

def refresh_ui(title: str, content: str):
    """
    刷新 OLED 界面：包含顶部标题栏和下方内容区（支持完整中文显示及换行）
    """
    oled.fill(0) # 清屏
    
    # 1. 绘制顶部标题 (Y=0 坐标)
    font.draw_text(oled, title, 0, 0)
    
    # 2. 绘制分割线 (Y=18)
    oled.hline(0, 18, 128, 1)
    
    # 3. 绘制主体内容 (Y=20 坐标，最大宽度 128px)
    font.draw_text(oled, content, 0, 20)
    
    # 4. 刷新屏幕
    oled.show()