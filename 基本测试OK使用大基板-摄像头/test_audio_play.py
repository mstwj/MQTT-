from audio_play import AudioPlayer

# 实例化播放器对象（默认引脚: SCK=20, WS=21, SD=19）
player = AudioPlayer()

# 调用实例方法播放音频
player.play_wav("tts_output.wav")