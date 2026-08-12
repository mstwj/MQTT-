import struct
import time
from array import array
from machine import I2S, Pin


def play_wav(filename, volume=1):
    """播放 WAV 文件并支持高性能软音量调节

    :param filename: 音频文件名
    :param volume: 音量大小，范围 0.0 到 1.0
    """
    with open(filename, "rb") as f:
        header = f.read(44)

        # 解析 WAV 核心参数
        num_channels = struct.unpack("<H", header[22:24])[0]
        sample_rate = struct.unpack("<I", header[24:28])[0]
        bits_per_sample = struct.unpack("<H", header[34:36])[0]

        # 动态判定声道格式
        audio_format = I2S.MONO if num_channels == 1 else I2S.STEREO

        i2s = I2S(
            0,
            sck=Pin(16),
            ws=Pin(15),
            sd=Pin(17),
            mode=I2S.TX,
            bits=bits_per_sample,
            format=audio_format,
            rate=sample_rate,
            ibuf=4096,
        )

        chunk_size = 2048
        # 音量映射系数 (0~256 整数乘法，比浮点数更快)
        vol_scale = int(max(0.0, min(1.0, volume)) * 256)

        try:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break

                # --- 高性能音量调节 ---
                if vol_scale < 256:
                    # 将 bytearray 转为 16位有符号整数数组 (内存高效)
                    samples = array("h", data)
                    for i in range(len(samples)):
                        samples[i] = (samples[i] * vol_scale) >> 8
                    data = samples

                i2s.write(data)

            # 给 DMA 缓冲区留出输出残余音频的时间
            time.sleep_ms(100)

        finally:
            i2s.deinit()


print("begin play")
play_wav("tts_output.wav")
print("play over")