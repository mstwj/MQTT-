import time
from micropython import const
import ustruct

# 命令定义
ST7789_NOP = const(0x00)
ST7789_SWRESET = const(0x01)
ST7789_SLPIN = const(0x10)
ST7789_SLPOUT = const(0x11)
ST7789_INVOFF = const(0x20)
ST7789_INVON = const(0x21)
ST7789_DISPOFF = const(0x28)
ST7789_DISPON = const(0x29)
ST7789_CASET = const(0x2A)
ST7789_RASET = const(0x2B)
ST7789_RAMWR = const(0x2C)
ST7789_MADCTL = const(0x36)
ST7789_COLMOD = const(0x3A)

# 颜色定义 (RGB565)
BLACK = const(0x0000)
BLUE = const(0x001F)
RED = const(0xF800)
GREEN = const(0x07E0)
CYAN = const(0x07FF)
MAGENTA = const(0xF81F)
YELLOW = const(0xFFE0)
WHITE = const(0xFFFF)


class ST7789:

    def __init__(
        self,
        spi,
        width,
        height,
        reset=None,
        dc=None,
        cs=None,
        backlight=None,
        rotation=0,
    ):
        self.spi = spi
        self.width = width
        self.height = height
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self.backlight = backlight

        if self.reset:
            self.reset.init(self.reset.OUT, value=1)
        if self.dc:
            self.dc.init(self.dc.OUT, value=0)
        if self.cs:
            self.cs.init(self.cs.OUT, value=1)
        if self.backlight:
            self.backlight.init(self.backlight.OUT, value=1)

        self.init()

    def _write(self, command, data=None):
        if self.cs:
            self.cs.value(0)

        if command is not None:
            self.dc.value(0)
            self.spi.write(bytearray([command]))

        if data:
            self.dc.value(1)
            self.spi.write(data)

        if self.cs:
            self.cs.value(1)

    def hard_reset(self):
        if self.reset:
            self.reset.value(1)
            time.sleep_ms(50)
            self.reset.value(0)
            time.sleep_ms(50)
            self.reset.value(1)
            time.sleep_ms(150)

    def init(self):
        self.hard_reset()
        self._write(ST7789_SWRESET)
        time.sleep_ms(150)
        self._write(ST7789_SLPOUT)
        time.sleep_ms(255)

        self._write(ST7789_COLMOD, b"\x55")  # 16-bit color
        time.sleep_ms(10)

        self._write(ST7789_MADCTL, b"\x00")  # 方向配置
        self._write(ST7789_INVON)  # 反色修正
        time.sleep_ms(10)

        self._write(ST7789_DISPON)
        time.sleep_ms(100)

    def set_window(self, x0, y0, x1, y1):
        self._write(
            ST7789_CASET, ustruct.pack(">HH", x0, x1)
        )  # 列地址设置
        self._write(
            ST7789_RASET, ustruct.pack(">HH", y0, y1)
        )  # 行地址设置
        self._write(ST7789_RAMWR)

    def fill(self, color):
        """用指定颜色刷屏"""
        self.set_window(0, 0, self.width - 1, self.height - 1)
        # 一次性写多像素提升刷屏效率
        chunk = ustruct.pack(">H", color) * 64
        num_pixels = self.width * self.height
        if self.cs:
            self.cs.value(0)
        self.dc.value(1)
        for _ in range(num_pixels // 64):
            self.spi.write(chunk)
        if self.cs:
            self.cs.value(1)
            
    def pixel(self, x, y, color):
        """画单个像素点"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.set_window(x, y, x, y)
            data = ustruct.pack(">H", color)
            if self.cs:
                self.cs.value(0)
            self.dc.value(1)
            self.spi.write(data)
            if self.cs:
                self.cs.value(1)

    def fill_rect(self, x, y, w, h, color):
        """绘制实心矩形"""
        x = max(0, min(x, self.width - 1))
        y = max(0, min(y, self.height - 1))
        w = max(1, min(w, self.width - x))
        h = max(1, min(h, self.height - y))

        self.set_window(x, y, x + w - 1, y + h - 1)
        chunk = ustruct.pack(">H", color) * 64
        num_pixels = w * h
        if self.cs:
            self.cs.value(0)
        self.dc.value(1)
        for _ in range(num_pixels // 64):
            self.spi.write(chunk)
        rem = num_pixels % 64
        if rem > 0:
            self.spi.write(ustruct.pack(">H", color) * rem)
        if self.cs:
            self.cs.value(1)

    def rect(self, x, y, w, h, color):
        """绘制空心矩形"""
        self.fill_rect(x, y, w, 1, color)
        self.fill_rect(x, y + h - 1, w, 1, color)
        self.fill_rect(x, y, 1, h, color)
        self.fill_rect(x + w - 1, y, 1, h, color)

    def text(self, font, text, x, y, color=WHITE, bg=BLACK):
        """使用 MicroPython 内置/8x8 字体绘制英文字符"""
        for char in text:
            if ord(char) < 128:
                # 使用内置点阵提取 (8x8)
                font_bytes = font.get_ch(char) if hasattr(font, "get_ch") else None
                # 如果没有第三方 font 库，可借助基础 bit 点阵画点
                for row in range(8):
                    for col in range(8):
                        # 简易画点展示 (建议配合 font 模块)
                        pass
            x += 8