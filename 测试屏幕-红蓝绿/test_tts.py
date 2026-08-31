import gc
import json
import urequests

# ================= 配置区 =================
API_KEY = "sk-lisenkrkcvdlmmavgytlsnpwpodcfyqrmnszopgzwpwespbe"
TEST_TEXT = "你好，我是 ESP32 语音助手，测试文本转语音功能成功。"
URL = "https://api.siliconflow.cn/v1/audio/speech"
# =========================================


def run_test():
    print("=" * 40)
    print("🚀 开始 TTS 专项测试...")
    print(f"📝 测试文本: '{TEST_TEXT}'")

    # ⚠️ 关键修正：换用 SiliconFlow 真正公开且免费的 CosyVoice2 模型
    payload = {
        "model": "FunAudioLLM/CosyVoice2-0.5B",
        "input": TEST_TEXT,
        "voice": "FunAudioLLM/CosyVoice2-0.5B:alex",  # CosyVoice2 专用音色
        "response_format": "mp3",
    }

    headers = {
        "Authorization": "Bearer " + API_KEY,
        "Content-Type": "application/json",
    }

    print("🌐 正在向 SiliconFlow 发送请求...")

    try:
        json_bytes = json.dumps(payload).encode("utf-8")
        response = urequests.post(URL, data=json_bytes, headers=headers)
        print(f"📡 收到响应，状态码: {response.status_code}")

        if response.status_code == 200:
            print("💾 成功！正在保存 mp3 文件 (test_out.mp3)...")
            with open("test_out.mp3", "wb") as f:
                f.write(response.content)
            response.close()
            gc.collect()

            print(
                "🎉 🎉 🎉 成功！mp3 文件下载成功！SiliconFlow 接口完全通畅！"
            )

        else:
            print(f"❌ 接口请求失败！状态码: {response.status_code}")
            print(f"📄 错误详情: {response.text}")
            response.close()

    except Exception as e:
        print("❌ 运行异常:", e)


run_test()