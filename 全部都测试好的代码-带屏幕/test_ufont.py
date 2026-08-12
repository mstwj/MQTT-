import framebuf
import ustruct
import time
from machine import SPI, Pin
import ufont  # 导入 uFont 库

class ST7789Display:
    def __init__(self, spi, width=240, height=320, reset=10, dc=9, cs=14, backlight=13):
        self.spi = spi
        self.width = width
        self.height = height
        self.reset = Pin(reset, Pin.OUT)
        self.dc = Pin(dc, Pin.OUT)
        self.cs = Pin(cs, Pin.OUT)
        self.backlight = Pin(backlight, Pin.OUT)

        self.backlight.value(1)
        self.reset.value(1)
        time.sleep_ms(50)
        self.reset.value(0)
        time.sleep_ms(50)
        self.reset.value(1)
        time.sleep_ms(150)

        # ST7789 初始化指令
        self._write_cmd(0x11)
        time.sleep_ms(120)
        self._write_cmd(0x3A, b"\x55")
        self._write_cmd(0x36, b"\x00")
        self._write_cmd(0x21)
        self._write_cmd(0x29)

        self.buffer = bytearray(self.width * self.height * 2)
        self.fb = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.RGB565)

    # 代理 uFont 需要用到的所有 FrameBuffer 方法与属性
    def pixel(self, *args, **kwargs):
        return self.fb.pixel(*args, **kwargs)

    def fill(self, *args, **kwargs):
        return self.fb.fill(*args, **kwargs)

    def rect(self, *args, **kwargs):
        return self.fb.rect(*args, **kwargs)

    def fill_rect(self, *args, **kwargs):
        return self.fb.fill_rect(*args, **kwargs)

    def blit(self, *args, **kwargs):
        return self.fb.blit(*args, **kwargs)

    def _write_cmd(self, cmd, data=None):
        self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytearray([cmd]))
        if data:
            self.dc.value(1)
            self.spi.write(data)
        self.cs.value(1)

    def show(self):
        self._write_cmd(0x2A, ustruct.pack(">HH", 0, self.width - 1))
        self._write_cmd(0x2B, ustruct.pack(">HH", 0, self.height - 1))
        self._write_cmd(0x2C)

        self.cs.value(0)
        self.dc.value(1)
        chunk_size = 4096
        for i in range(0, len(self.buffer), chunk_size):
            self.spi.write(self.buffer[i : i + chunk_size])
        self.cs.value(1)

# ==========================================
# 运行 uFont 动态中文测试
# ==========================================
print("1. 初始化 SPI 屏幕...")
spi = SPI(1, baudrate=40000000, sck=Pin(12), mosi=Pin(11), miso=None)
lcd = ST7789Display(spi=spi, width=240, height=320, reset=10, dc=9, cs=14, backlight=13)

print("2. 加载 uFont 字体...")
font = ufont.BMFont("unifont-14-12917-16.v3.bmf")

print("3. 绘制文字...")
lcd.fill(0x0000)

# 直接传入补全了 width, height, blit 的 lcd 对象
font.text(lcd, "智能语音助手", 10, 20, color=0xFFE0)
font.text(lcd, "你好！我是你的 AI 助手，现在任意中文都可以正常动态显示了，告别乱码！", 10, 60, color=0xFFFF, show_width=220)

lcd.show()
print("✅ uFont 测试完成，无乱码动态中文显示成功！")