import json
import urequests

SILICONFLOW_KEY = "sk-lisenkrkcvdlmmavgytlsnpwpodcfyqrmnszopgzwpwespbe"
SILICONFLOW_URL = "https://api.siliconflow.cn/v1/chat/completions"
# 推荐使用 V3/V2.5 等非 R1 推理模型，速度提升 5~10 倍
MODEL_NAME = "deepseek-ai/DeepSeek-V3"

HEADERS = {
    "Authorization": "Bearer " + SILICONFLOW_KEY,
    "Content-Type": "application/json",
}


def chat_ask(user_content: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "Answer directly in plain English without thinking process. Keep within 20 words.",
            },
            {"role": "user", "content": user_content},
        ],
        "max_tokens": 64,  # ESP32 内存小，尽量限制生成长度（加速返回）
        "temperature": 0.3,
        # 关键！SiliconFlow 平台关闭 DeepSeek 推理/思维链强行加速
        "enable_thinking": False,
    }

    resp = None
    try:
        json_bytes = json.dumps(payload).encode("utf-8")
        print("Sending Payload Size:", len(json_bytes))

        # 核心修复：urequests 不支持 timeout 参数，改为直接通过 post 发送
        # 若仍超时，建议模型改用 speed 极快的 "Qwen/Qwen2.5-7B-Instruct"
        resp = urequests.post(SILICONFLOW_URL, headers=HEADERS, data=json_bytes)

        if resp.status_code == 200:
            data = resp.json()
            if "choices" in data and len(data["choices"]) > 0:
                msg = data["choices"][0]["message"]
                content = msg.get("content", "").strip()
                return content
            return "No content"
        else:
            return f"HTTP {resp.status_code}: {resp.text[:30]}"

    except Exception as e:
        print("API Exception:", e)
        return f"Error:{str(e)}"
    finally:
        if resp:
            try:
                resp.close()
            except:
                pass