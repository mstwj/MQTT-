from machine import I2S, Pin
import struct
import time


class AudioRecorder:

    def __init__(self, sck_pin=5, ws_pin=6, sd_pin=4, sample_rate=16000):
        """初始化 I2S 麦克风"""
        self.sample_rate = sample_rate
        self.sck_pin = sck_pin
        self.ws_pin = ws_pin
        self.sd_pin = sd_pin

        # 核心修改点：麦克风采集必须设为 I2S.STEREO，避免数据位错位
        self.audio_in = I2S(
            0,
            sck=Pin(self.sck_pin),
            ws=Pin(self.ws_pin),
            sd=Pin(self.sd_pin),
            mode=I2S.RX,
            bits=16,
            format=I2S.STEREO,  # <-- 修改这里：从 MONO 改为 STEREO
            rate=self.sample_rate,
            ibuf=4096,
        )

    def _create_wav_header(self, pcm_len, channels=2, bits_per_sample=16):
        """生成 44 字节标准 WAV 文件头"""
        # 注意：因为以 STEREO 采集，channels 改为 2
        byte_rate = self.sample_rate * channels * (bits_per_sample // 8)
        block_align = channels * (bits_per_sample // 8)

        header = bytearray(44)
        header[0:4] = b"RIFF"
        struct.pack_into("<I", header, 4, pcm_len + 36)
        header[8:12] = b"WAVE"
        header[12:16] = b"fmt "
        struct.pack_into("<I", header, 16, 16)
        struct.pack_into("<H", header, 20, 1)  # PCM
        struct.pack_into("<H", header, 22, channels)  # 2 声道
        struct.pack_into("<I", header, 24, self.sample_rate)
        struct.pack_into("<I", header, 28, byte_rate)
        struct.pack_into("<H", header, 32, block_align)
        struct.pack_into("<H", header, 34, bits_per_sample)
        header[36:40] = b"data"
        struct.pack_into("<I", header, 40, pcm_len)
        return header

    def record_to_wav(self, filename, button_pin):
        """流式录音并保存为 WAV"""
        buf = bytearray(2048)
        total_pcm_bytes = 0

        print(f"🎙️ 开始录音，保存至 {filename} ...")

        with open(filename, "wb") as f:
            f.write(bytearray(44))

            while button_pin.value() == 0:
                num_read = self.audio_in.readinto(buf)
                if num_read > 0:
                    f.write(buf[:num_read])
                    total_pcm_bytes += num_read

            f.seek(0)
            # 传入 channels=2
            header = self._create_wav_header(
                total_pcm_bytes, channels=2, bits_per_sample=16
            )
            f.write(header)

        # 2 声道、16-bit 计费公式
        duration = total_pcm_bytes / (self.sample_rate * 4)
        print(
            f"⏹️ 录音完成！时长: {duration:.1f}s, 文件总大小: {total_pcm_bytes + 44} 字节"
        )

    def close(self):
        """释放 I2S 硬件资源"""
        self.audio_in.deinit()