import struct
import time
from machine import I2S, Pin


class AudioRecorder:

    def __init__(self, sck_pin=5, ws_pin=6, sd_pin=4, sample_rate=16000):
        self.sample_rate = sample_rate
        self.sck_pin = sck_pin
        self.ws_pin = ws_pin
        self.sd_pin = sd_pin
        self.audio_in = None

    def _init_i2s(self):
        """动态初始化 I2S 硬件，带重试机制以防总线冲突"""
        for retry in range(3):
            try:
                # 尝试初始化 I2S 0
                return I2S(
                    0,
                    sck=Pin(self.sck_pin),
                    ws=Pin(self.ws_pin),
                    sd=Pin(self.sd_pin),
                    mode=I2S.RX,
                    bits=16,
                    format=I2S.STEREO,  # 硬件底层维持 STEREO 规避错位
                    rate=self.sample_rate,
                    ibuf=4096,
                )
            except OSError as e:
                # 若硬件通道被播音或其他进程占用，稍等后重试
                time.sleep_ms(100)
                if retry == 2:
                    raise e

    def _create_wav_header(self, pcm_len, channels=1, bits_per_sample=16):
        """生成标准 WAV 文件头，默认设为单声道(channels=1)"""
        byte_rate = self.sample_rate * channels * (bits_per_sample // 8)
        block_align = channels * (bits_per_sample // 8)

        header = bytearray(44)
        header[0:4] = b"RIFF"
        struct.pack_into("<I", header, 4, pcm_len + 36)
        header[8:12] = b"WAVE"
        header[12:16] = b"fmt "
        struct.pack_into("<I", header, 16, 16)
        struct.pack_into("<H", header, 20, 1)  # PCM
        struct.pack_into("<H", header, 22, channels)  # 1 单声道
        struct.pack_into("<I", header, 24, self.sample_rate)
        struct.pack_into("<I", header, 28, byte_rate)
        struct.pack_into("<H", header, 32, block_align)
        struct.pack_into("<H", header, 34, bits_per_sample)
        header[36:40] = b"data"
        struct.pack_into("<I", header, 40, pcm_len)
        return header

    def record_to_wav(self, filename, button_pin, max_seconds=50):
        """流式录音：按需开启 I2S，过滤开局噪音，并在结束时彻底释放硬件"""
        # 1. 动态开启硬件
        self.audio_in = self._init_i2s()

        raw_buf = bytearray(2048)
        # 预分配 mono_buf 避免在 while 循环中重复创建内存导致 OOM
        mono_buf = bytearray(1024)
        total_pcm_bytes = 0

        # 【核心新增】计算最大允许的单声道 PCM 字节数（采样率 * 2字节 * 秒数）
        max_pcm_bytes = self.sample_rate * 2 * max_seconds

        try:
            # 2. 丢弃前 3 个 Buffer 的初始空/噪数据（麦克风预热）
            for _ in range(3):
                self.audio_in.readinto(raw_buf)

            print(
                f"🎙️ 开始录音，保存至 {filename} (最长限制 {max_seconds} 秒)..."
            )

            with open(filename, "wb") as f:
                f.write(bytearray(44))  # 预留 WAV 头

                # 【核心修改】循环条件加上 total_pcm_bytes < max_pcm_bytes 限制
                while (
                    button_pin.value() == 0 and total_pcm_bytes < max_pcm_bytes
                ):
                    num_read = self.audio_in.readinto(raw_buf)
                    if num_read > 0:
                        # 提取单声道数据 (取 STEREO 中的左声道 2 字节)
                        idx = 0
                        for i in range(0, num_read, 4):
                            mono_buf[idx] = raw_buf[i]
                            mono_buf[idx + 1] = raw_buf[i + 1]
                            idx += 2

                        # 使用 memoryview 只切片实际读取到的字节数，复用 mono_buf
                        f.write(memoryview(mono_buf)[:idx])
                        total_pcm_bytes += idx

                # 回填单声道 WAV 头
                f.seek(0)
                header = self._create_wav_header(
                    total_pcm_bytes, channels=1, bits_per_sample=16
                )
                f.write(header)

            duration = total_pcm_bytes / (self.sample_rate * 2)
            print(
                f"⏹️ 录音完成！时长: {duration:.1f}s, 文件大小:"
                f" {total_pcm_bytes + 44} 字节"
            )

        finally:
            # 3. 无论录音成功还是异常，必须关闭并释放 I2S，避免阻塞 AudioPlayer
            self.close()

    def close(self):
        """彻底反初始化 I2S 外设并留出总线缓冲时间"""
        if self.audio_in is not None:
            try:
                self.audio_in.deinit()
            except Exception:
                pass
            self.audio_in = None
            time.sleep_ms(100)  # 释放硬件总线，确保播放端可无缝接管