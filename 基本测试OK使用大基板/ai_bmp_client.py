import gc
import json
import urequests

# 1. API 秘钥与接口配置（已补全 Bearer 前缀，解决 401 Token invalid 问题）
SILICONFLOW_KEY = "sk-lisenkrkcvdlmmavgytlsnpwpodcfyqrmnszopgzwpwespbe"
API_KEY = "Bearer " + SILICONFLOW_KEY
IMAGE_URL = "https://api.siliconflow.cn/v1/images/generations"

SAVE_PATH = "test.bmp"  # 存储在 ESP32-S3 Flash 中的文件名


def generate_and_download_image(prompt_text, save_filename=SAVE_PATH):
    """根据提示词请求 AI 生图，并直接流式下载保存至 ESP32-S3 文件系统"""
    headers = {"Authorization": API_KEY, "Content-Type": "application/json"}

    # 构建生图 Payload
    payload = {
        "model": "Kwai-Kolors/Kolors",
        "prompt": prompt_text,
        "image_size": "768x1024",  # 云端最低标准尺寸
        "batch_size": 1,
        "num_inference_steps": 20,
        "guidance_scale": 7.5,
    }

    resp = None
    down_resp = None

    print("1. 正在发送 AI 生图请求...")
    try:
        # 手动序列化为 UTF-8 字节数据，避免 MicroPython 编码报错
        data_bytes = json.dumps(payload).encode("utf-8")

        # 发起生图 POST 请求
        resp = urequests.post(IMAGE_URL, headers=headers, data=data_bytes)

        if resp.status_code == 200:
            result = resp.json()
            if "images" in result and len(result["images"]) > 0:
                img_url = result["images"][0]["url"]
                print("2. 生图成功！图片网络地址:", img_url)

                # 关闭第一个 API 请求响应，回收内存
                resp.close()
                resp = None
                gc.collect()

                # 发起 GET 请求下载图片文件
                print(f"3. 正在下载图片并保存至 {save_filename} ...")
                down_resp = urequests.get(img_url)

                if down_resp.status_code == 200:
                    # 分块写入 Flash，防止 1024x1024 的大图导致 ESP32 内存溢出 (OOM)
                    with open(save_filename, "wb") as f:
                        while True:
                            chunk = down_resp.raw.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)

                    print(
                        f"4. 下载成功！图片已成功存入 ESP32: {save_filename}"
                    )
                    return True
                else:
                    print("下载图片失败，状态码:", down_resp.status_code)
                    return False
            else:
                print("解析失败，未找到图片 URL 地址")
                return False
        else:
            print(
                f"请求生图 API 失败，HTTP {resp.status_code}: {resp.text}"
            )
            return False

    except Exception as e:
        print("生图与下载过程出现异常:", e)
        return False

    finally:
        # 严格清理所有网络连接，避免 ESP32 内存泄露
        if resp:
            try:
                resp.close()
            except:
                pass
        if down_resp:
            try:
                down_resp.close()
            except:
                pass
        gc.collect()


# 独立测试入口
if __name__ == "__main__":
    # 如果单独运行本脚本测试，请确保 ESP32 已在主程序连上 WiFi
    generate_and_download_image("一只可爱的小猪, pixel art style")