# display_ui.py - ST7789 + uFont 界面、自动换行排版与状态封装模块

import framebuf
import ustruct
import time
from machine import SPI, Pin
import ufont


class ST7789Display:
    """ST7789 屏幕底层驱动与 uFont 方法代理类"""

    def __init__(self, spi, width=240, height=320, reset=10, dc=9, cs=14, backlight=13):
        self.spi = spi
        self.width = width
        self.height = height
        self.reset = Pin(reset, Pin.OUT)
        self.dc = Pin(dc, Pin.OUT)
        self.cs = Pin(cs, Pin.OUT)
        self.backlight = Pin(backlight, Pin.OUT)

        # 复位并开背光
        self.backlight.value(1)
        self.reset.value(1)
        time.sleep_ms(50)
        self.reset.value(0)
        time.sleep_ms(50)
        self.reset.value(1)
        time.sleep_ms(150)

        # ST7789 初始化指令序列
        self._write_cmd(0x11)
        time.sleep_ms(120)
        self._write_cmd(0x3A, b"\x55")
        self._write_cmd(0x36, b"\x08")
        self._write_cmd(0x21)
        self._write_cmd(0x29)

        # 显存 FrameBuffer 初始化
        self.buffer = bytearray(self.width * self.height * 2)
        self.fb = framebuf.FrameBuffer(
            self.buffer, self.width, self.height, framebuf.RGB565
        )

    # 代理 uFont 渲染所需的方法
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
        """将 Buffer 缓冲区图像一次性刷入屏幕"""
        self._write_cmd(0x2A, ustruct.pack(">HH", 0, self.width - 1))
        self._write_cmd(0x2B, ustruct.pack(">HH", 0, self.height - 1))
        self._write_cmd(0x2C)

        self.cs.value(0)
        self.dc.value(1)
        chunk_size = 4096
        for i in range(0, len(self.buffer), chunk_size):
            self.spi.write(self.buffer[i : i + chunk_size])
        self.cs.value(1)


class UIManager:
    """UI 界面与长文本自动折行算法高层封装类"""

    def __init__(self, font_path="unifont-14-12917-16.v3.bmf"):
        # 初始化 SPI 总线与屏幕硬件 (根据需要可在此调整引脚)
        spi = SPI(1, baudrate=40000000, sck=Pin(12), mosi=Pin(11), miso=None)
        self.lcd = ST7789Display(
            spi=spi, width=240, height=320, reset=10, dc=9, cs=14, backlight=13
        )

        # 加载 uFont 字体解析器
        self.font = ufont.BMFont(font_path)

    def draw_text_wrap(
        self,
        text,
        x=10,
        y=50,
        max_chars_per_line=12,
        line_height=20,
        color=0xFFFF,
    ):
        """精准手动换行算法（解决多汉字超过宽度不换行、显示不全的问题）"""
        lines = text.split("\n")  # 拆分显式换行符 \n
        curr_y = y

        for line in lines:
            if not line:
                curr_y += line_height
                continue

            # 每行超过 max_chars_per_line 个字自动切片折行
            for i in range(0, len(line), max_chars_per_line):
                sub_text = line[i : i + max_chars_per_line]

                # 防越界：超出屏幕下方可视范围不再绘制
                if curr_y > 300:
                    break

                # 调用 uFont 渲染这一行切片后的子字符串
                self.font.text(self.lcd, sub_text, x, curr_y, color=color)
                curr_y += line_height  # 累加行高向下推移

    def render(self, title, content="", color=0xFFFF):
        """统一界面绘制对外主接口"""
        self.lcd.fill(0x0000)  # 黑色背景清屏

        # 1. 绘制顶部标题栏（黄色文字 + 蓝高亮分割线）
        self.font.text(self.lcd, title, 10, 15, color=0xFFE0)
        self.lcd.fb.hline(10, 38, 220, 0x07FF)

        # 2. 绘制主体正文（支持无限长度的中英文文本自动多行折行）
        if content:
            self.draw_text_wrap(
                content,
                x=10,
                y=50,
                max_chars_per_line=12,  # 240 宽度屏，扣去边距每行最多容纳 12 个 16px 汉字
                line_height=20,         # 行间距
                color=color,
            )

        # 3. 刷屏显示
        self.lcd.show()