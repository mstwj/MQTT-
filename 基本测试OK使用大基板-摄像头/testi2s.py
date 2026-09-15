from machine import I2S, Pin
import time

i2s = I2S(
    0,
    sck=Pin(47),
    ws=Pin(21),
    sd=Pin(38),
    mode=I2S.RX,
    bits=16,
    format=I2S.STEREO,
    rate=16000,
    ibuf=4096,
)

buf = bytearray(256)
print("请对着麦克风用力吹一口气或敲击桌面...")

try:
    for i in range(10):
        i2s.readinto(buf)
        # 看看前 16 个字节的数值
        print(f"采样{i+1}:", list(buf[:16]))
        time.sleep(0.3)
finally:
    i2s.deinit()