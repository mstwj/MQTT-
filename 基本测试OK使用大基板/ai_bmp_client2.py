import gc
import json
import urequests


def url_encode(s):
    """URL 编码函数"""
    res = []
    for c in str(s):
        if (
            ("a" <= c <= "z")
            or ("A" <= c <= "Z")
            or ("0" <= c <= "9")
            or c in "-_.~"
        ):
            res.append(c)
        else:
            res.append("%%%02X" % ord(c))
    return "".join(res)


class AIBMPClient:

    def __init__(self):
        self.api_url = "https://api.siliconflow.cn/v1/images/generations"
        self.api_key = "sk-lisenkrkcvdlmmavgytlsnpwpodcfyqrmnszopgzwpwespbe"
        self.model = "Tongyi-MAI/Z-Image"

    def _get_siliconflow_url(self, prompt, status_cb=None):
        """步骤 1：请求 SiliconFlow 生成图片 URL"""
        if status_cb:
            status_cb("AI 绘图中", "🤖 正在请求 AI 大模型生成图片...")

        clean_prompt = str(prompt).strip().replace("\n", " ").replace("\r", "")
        print("🎨 最终发送给 AI 的提示词:", clean_prompt)

        payload = {"model": self.model, "prompt": clean_prompt}

        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
        }

        gc.collect()
        json_bytes = json.dumps(payload).encode("utf-8")
        resp = urequests.post(self.api_url, headers=headers, data=json_bytes)

        if resp.status_code != 200:
            err_msg = resp.text
            resp.close()
            print("❌ SiliconFlow 返回错误详情:", err_msg)
            raise RuntimeError("AI生图失败: " + str(resp.status_code))

        data = resp.json()
        resp.close()
        gc.collect()

        img_url = None
        for key in ("images", "data"):
            arr = data.get(key)
            if isinstance(arr, list) and len(arr) > 0:
                img_url = arr[0].get("url")
                if img_url:
                    break

        if not img_url:
            raise RuntimeError("生图响应中未找到图片 URL")

        return img_url

    def _convert_and_download_bmp(
        self, img_url, save_path="output.bmp", status_cb=None
    ):
        """步骤 2：使用适配微控制器的图床 API 直接获取 16-bit/24-bit 原始 BMP"""
        if status_cb:
            status_cb("AI 绘图中", "⚙️ 正在云端转码并下载 240x320 BMP...")

        # 换用更加稳定且无防盗链拦截的图像转码 Endpoint，强制转换为标准 240x320 BMP 格式
        proxy_url = "https://images.weserv.nl/?url={}&w=240&h=320&fit=cover&output=bmp".format(
            url_encode(img_url)
        )

        gc.collect()
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        }

        resp = urequests.get(proxy_url, headers=headers, stream=True)

        if resp.status_code != 200:
            err_text = resp.text
            resp.close()
            print("❌ 转码服务端错误响应:", err_text)
            raise RuntimeError("云端转码失败: " + str(resp.status_code))

        # 校验文件头：读取前 2 字节必须为 'BM'
        first_chunk = resp.raw.read(1024)
        if not first_chunk or not first_chunk.startswith(b"BM"):
            resp.close()
            print("❌ 转码数据校验失败：接收到的响应非真实 BMP 文件！")
            raise RuntimeError("云端返回数据格式非法(非BMP)")

        # 校验通过，写入本地文件
        with open(save_path, "wb") as f:
            f.write(first_chunk)
            while True:
                chunk = resp.raw.read(1024)
                if not chunk:
                    break
                f.write(chunk)

        resp.close()
        gc.collect()
        return save_path

    def generate_image(self, prompt, save_bmp_path="output.bmp", status_cb=None):
        raw_url = self._get_siliconflow_url(prompt, status_cb=status_cb)
        return self._convert_and_download_bmp(
            raw_url, save_bmp_path, status_cb=status_cb
        )