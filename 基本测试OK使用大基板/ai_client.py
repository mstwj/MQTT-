import gc
import json
import urequests

SILICONFLOW_KEY = "sk-lisenkrkcvdlmmavgytlsnpwpodcfyqrmnszopgzwpwespbe"
SILICONFLOW_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL_NAME = "deepseek-ai/DeepSeek-V4-Flash"

HEADERS = {
    "Authorization": "Bearer " + SILICONFLOW_KEY,
    "Content-Type": "application/json; charset=utf-8",
}


def chat_ask(user_content: str) -> str:
    gc.collect()

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一个智能语音助手。请用自然、口语化的中文回答用户问题。"
                    "回答必须简洁明了，字数控制在 120 字以内。"
                    "请切记：严禁使用 Emoji 表情符号、颜文字或特殊的 MarkDown 标点。"
                ),
            },
            {"role": "user", "content": user_content},
        ],
        "max_tokens": 128,
        "temperature": 0.3,
        #"enable_thinking": False,
    }

    resp = None
    try:
        # 将 dict 编码为 UTF-8 bytes 字节流
        payload_bytes = json.dumps(payload).encode("utf-8")
        print("Sending Payload Size:", len(payload_bytes))

        resp = urequests.post(
            SILICONFLOW_URL, headers=HEADERS, data=payload_bytes, timeout=30
        )

        if resp.status_code == 200:
            data = resp.json()
            if "choices" in data and len(data["choices"]) > 0:
                msg = data["choices"][0]["message"]
                content = msg.get("content", "").strip()
                return content
            return "No content"
        else:
            print(f"❌ AI HTTP 错误: {resp.status_code}, 响应: {resp.text}")
            return f"HTTP {resp.status_code}"

    except OSError as e:
        print(f"⚠️ 网络请求超时或异常: {e}")
        return "网络响应超时，请重试"
    except Exception as e:
        print("❌ AI API Exception:", e)
        return f"Error:{str(e)}"
    finally:
        if resp:
            try:
                resp.close()
            except:
                pass
        gc.collect()