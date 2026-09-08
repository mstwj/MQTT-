import sys
sys.implementation

try:
    import camera
    print("✅ 恭喜！当前固件内置了 camera 模块")
except ImportError:
    print("❌ 当前固件不支持 camera 模块，需要重新刷固件")