# display_ui.py - 纯原生支持，已完全修正 320x240 横屏与 BMP 图像渲染花屏问题
import framebuf
import ufont
import ustruct
import time
from machine import SPI, Pin


class ST7789Display:
    """ST7789 屏幕底层驱动与代理类"""

    def __init__(
        self,
        spi,
        width=320,
        height=240,
        reset=41,
        dc=42,
        cs=2,
        backlight=1,
    ):
        self.spi = spi
        self.width = width
        self.height = height
        self.reset = Pin(reset, Pin.OUT) if reset is not None else None
        self.dc = Pin(dc, Pin.OUT)
        self.cs = Pin(cs, Pin.OUT) if cs is not None else None
        self.backlight = Pin(backlight, Pin.OUT) if backlight is not None else None

        # ================= 硬件物理级硬复位 =================
        if self.backlight:
            self.backlight.value(1)  # 强行点亮背光
        if self.cs:
            self.cs.value(1)  # 释放片选总线

        if self.reset:
            self.reset.value(1)  # 先拉高
            time.sleep_ms(50)
            self.reset.value(0)  # 强行拉低硬件复位 100ms
            time.sleep_ms(100)
            self.reset.value(1)  # 重新拉高，屏幕芯片唤醒完毕
            time.sleep_ms(100)
        # ====================================================

        # ST7789 初始化指令序列
        self._write_cmd(0x11)
        time.sleep_ms(120)
        self._write_cmd(0x3A, b"\x55")  # 16-bit RGB565

        # 横屏方向控制 MADCTL: 0x70
        self._write_cmd(0x36, b"\x70")
        self._write_cmd(0x21)  # IPS 屏使能反色
        self._write_cmd(0x29)  # 开启显示

        # 显存 Buffer 分配: 320x240x2 = 153,600 字节
        self.buffer = bytearray(self.width * self.height * 2)
        self.fb = framebuf.FrameBuffer(
            self.buffer, self.width, self.height, framebuf.RGB565
        )

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
        if self.cs:
            self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytearray([cmd]))
        if data:
            self.dc.value(1)
            self.spi.write(data)
        if self.cs:
            self.cs.value(1)

    def show(self):
        """将 Buffer 缓冲区图像刷入屏幕"""
        self._write_cmd(0x2A, ustruct.pack(">HH", 0, self.width - 1))
        self._write_cmd(0x2B, ustruct.pack(">HH", 0, self.height - 1))
        self._write_cmd(0x2C)

        if self.cs:
            self.cs.value(0)
        self.dc.value(1)

        # 逐像素交换相邻的 2 个字节（小端序 -> 大端序）
        buf_len = len(self.buffer)
        swapped_buf = bytearray(buf_len)

        for i in range(0, buf_len, 2):
            swapped_buf[i] = self.buffer[i + 1]
            swapped_buf[i + 1] = self.buffer[i]

        chunk_size = 4096
        for i in range(0, buf_len, chunk_size):
            self.spi.write(swapped_buf[i : i + chunk_size])

        if self.cs:
            self.cs.value(1)

    def push_camera_buf(self, buf, w=320, h=240):
        """零拷贝/极速直推：直接将 320x240 raw buf 覆盖全屏硬件显存"""
        self._write_cmd(0x2A, ustruct.pack(">HH", 0, w - 1))
        self._write_cmd(0x2B, ustruct.pack(">HH", 0, h - 1))
        self._write_cmd(0x2C)

        if self.cs:
            self.cs.value(0)
        self.dc.value(1)

        self.spi.write(buf)

        if self.cs:
            self.cs.value(1)

    def display_ai_bmp(self, filename="photo.bmp"):
        """直接显示后端返回的标准 16位 RAW BMP 图片"""
        try:
            with open(filename, "rb") as f:
                f.seek(54)  # 跳过 54 字节文件头
                bmp_data = bytearray(f.read(320 * 240 * 2))

            if not bmp_data or len(bmp_data) != 320 * 240 * 2:
                print("❌ AI 图片数据长度不匹配，无法显示")
                return

            # 原生字节高低位调换
            for i in range(0, len(bmp_data), 2):
                bmp_data[i], bmp_data[i + 1] = bmp_data[i + 1], bmp_data[i]

            self.push_camera_buf(bmp_data, 320, 240)
            print("✅ AI 图像已成功刷屏！")

        except Exception as e:
            print(f"❌ 渲染 AI 图像异常: {e}")

    def draw_bmp(self, filename, start_x=0, start_y=0):
        """完全修正版 BMP 解析：兼容 16位/24位，彻底消除花屏与偏色"""
        try:
            with open(filename, "rb") as f:
                if f.read(2) != b"BM":
                    print("❌ 不是有效的 BMP 文件！")
                    return

                f.seek(10)
                data_offset = ustruct.unpack("<I", f.read(4))[0]
                f.seek(18)
                width = ustruct.unpack("<i", f.read(4))[0]
                raw_height = ustruct.unpack("<i", f.read(4))[0]
                f.seek(28)
                bpp = ustruct.unpack("<H", f.read(2))[0]

                height = abs(raw_height)
                f.seek(data_offset)

                # ------------ 16 位 RGB565（摄像头/AI生成的 16位 BMP）------------
                if bpp == 16:
                    bmp_data = bytearray(f.read(width * height * 2))
                    
                    # 进行大小端字节转换（防止图像颜色混乱发紫发绿）
                    for i in range(0, len(bmp_data), 2):
                        bmp_data[i], bmp_data[i + 1] = (
                            bmp_data[i + 1],
                            bmp_data[i],
                        )

                    # 全屏 320x240 且从 (0,0) 开始时，直接调用 SPI 直推（避免花屏与撕裂）
                    if start_x == 0 and start_y == 0 and width == self.width and height == self.height:
                        self.push_camera_buf(bmp_data, width, height)
                    else:
                        img_fb = framebuf.FrameBuffer(
                            bmp_data, width, height, framebuf.RGB565
                        )
                        self.fb.blit(img_fb, start_x, start_y)
                        self.show()

                    print("✅ 16位 BMP 图像渲染成功！")

                # ------------ 24 位 RGB888（PC/PhotoShop 导出的 BMP）------------
                elif bpp == 24:
                    row_bytes = (width * 3 + 3) & ~3  # 4 字节对齐
                    line_buf = bytearray(width * 2)
                    line_fb = framebuf.FrameBuffer(
                        line_buf, width, 1, framebuf.RGB565
                    )

                    for y in range(height):
                        row_data = f.read(row_bytes)
                        if not row_data:
                            break
                        for x in range(width):
                            idx = x * 3
                            b, g, r = (
                                row_data[idx],
                                row_data[idx + 1],
                                row_data[idx + 2],
                            )
                            # RGB888 -> RGB565 位运算
                            rgb565 = (
                                ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                            )
                            # 高低字节对调存入
                            line_buf[x * 2] = (rgb565 >> 8) & 0xFF
                            line_buf[x * 2 + 1] = rgb565 & 0xFF

                        # 24位正高度 BMP 存储方向通常是上下颠倒的，需倒序绘制
                        target_y = (
                            start_y + (height - 1 - y)
                            if raw_height > 0
                            else start_y + y
                        )
                        self.fb.blit(line_fb, start_x, target_y)

                    self.show()
                    print("✅ 24位 BMP 图像渲染成功！")

                else:
                    print(f"⚠️ 暂不支持的色深: {bpp}bpp")

        except Exception as e:
            print("❌ BMP 显示失败:", e)

    def draw_buffer(self, buf, width, height, start_x=0, start_y=0):
        """直接将内存中的 RGB565 字节流渲染到指定位置"""
        try:
            img_fb = framebuf.FrameBuffer(
                bytearray(buf), width, height, framebuf.RGB565
            )
            self.fb.blit(img_fb, start_x, start_y)
        except Exception as e:
            print("内存图像渲染失败:", e)


class UIManager:
    """UI 界面高层封装"""

    def __init__(self, font_path="unifont-14-12917-16.v3.bmf"):
        # 配置 SPI：SCL=GPIO39, SDA=GPIO40
        spi = SPI(1, baudrate=40000000, sck=Pin(39), mosi=Pin(40), miso=None)

        self.lcd = ST7789Display(
            spi=spi, width=320, height=240, reset=41, dc=42, cs=2, backlight=1
        )
        self.font = ufont.BMFont(font_path)

    def show_text(self, text, x=10, y=10, color=0xFFFF, bg_color=None, size=16):
        """在当前屏幕指定位置直接绘制文字并刷屏展示"""
        try:
            if bg_color is not None:
                text_len = len(text) * (size // 2)
                self.lcd.fill_rect(x, y, text_len, size + 4, bg_color)

            self.font.text(self.lcd, text, x, y, color=color)
            self.lcd.show()
        except Exception as e:
            print("显示文字失败:", e)

    def draw_text_wrap(
        self, text, x=10, y=50, max_width=300, line_height=22, color=0xFFFF
    ):
        """根据屏幕实际像素宽度 (max_width=300) 进行智能自动换行"""
        lines = text.split("\n")
        curr_y = y

        char_w_cn = 16
        char_w_en = 8

        for line in lines:
            if not line:
                curr_y += line_height
                continue

            current_sub_line = ""
            current_px_width = 0

            for char in line:
                char_w = char_w_en if ord(char) < 128 else char_w_cn

                if current_px_width + char_w > max_width:
                    if curr_y > 210:  # 触底防护
                        break
                    self.font.text(
                        self.lcd, current_sub_line, x, curr_y, color=color
                    )
                    curr_y += line_height
                    current_sub_line = char
                    current_px_width = char_w
                else:
                    current_sub_line += char
                    current_px_width += char_w

            if current_sub_line and curr_y <= 210:
                self.font.text(
                    self.lcd, current_sub_line, x, curr_y, color=color
                )
                curr_y += line_height

    def render(self, title, content="", color=0xFFFF):
        """刷新全屏 UI 页面"""
        self.lcd.fill(0x0000)  # 清除全屏显存
        self.font.text(self.lcd, title, 10, 15, color=0xFFE0)
        self.lcd.fb.hline(10, 38, 300, 0x07FF)  # 分割线
        if content:
            self.draw_text_wrap(
                content, x=10, y=50, max_width=300, line_height=22, color=color
            )
        self.lcd.show()

    def draw_rec_dot(self, show=True):
        """在右上角绘制/清除录音指示红点"""
        if show:
            self.lcd.fill_rect(290, 15, 12, 12, 0xF800)
        else:
            self.lcd.fill_rect(290, 15, 12, 12, 0x0000)
        self.lcd.show()