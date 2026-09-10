import gc
import json
import os
import time
import urequests


class AIBMPClient:

    def __init__(self):
        # 1. 硅基流动 AI 生图配置
        self.sf_api_url = "https://api.siliconflow.cn/v1/images/generations"
        self.sf_api_key = (
            "sk-lisenkrkcvdlmmavgytlsnpwpodcfyqrmnszopgzwpwespbe"
        )
        self.sf_model = "Tongyi-MAI/Z-Image"
        self.sf_image_size = "768x1024"

        # 2. 后端的转码接口
        self.convert_url = "https://www.passnow.tech/convert.php"

        self.ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )

    def _generate_png_url(self, prompt):
        """步骤 1：请求硅基流动生图，获取图片 URL"""
        clean_prompt = str(prompt).strip().replace("\n", " ").replace("\r", "")
        print("🎨 1. 正在调用 AI 生图接口... 提示词:", clean_prompt)

        payload = {
            "model": self.sf_model,
            "prompt": clean_prompt,
            "image_size": self.sf_image_size,
        }
        headers = {
            "Authorization": "Bearer " + self.sf_api_key,
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": self.ua,
        }

        gc.collect()
        json_bytes = json.dumps(payload).encode("utf-8")
        resp = urequests.post(self.sf_api_url, headers=headers, data=json_bytes)

        if resp.status_code != 200:
            err_msg = resp.text
            resp.close()
            print("❌ AI 生图接口报错:", err_msg[:200])
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
            raise RuntimeError("响应中未找到图片 URL")

        print("🔗 获取到原始图片 URL:", img_url[:60] + "...")
        return img_url

    def _download_png_bytes(self, png_url):
        """步骤 2：下载原始 PNG 二进制图片存入 8MB PSRAM 内存"""
        print("📥 2. 正在把原始 PNG 图片完整下载到 ESP32-S3 内存中...")
        gc.collect()

        resp = urequests.get(png_url, headers={"User-Agent": self.ua})
        if resp.status_code != 200:
            resp.close()
            raise RuntimeError(f"下载 PNG 失败，状态码: {resp.status_code}")

        img_bytes = resp.content
        resp.close()
        gc.collect()

        print(
            f"✅ PNG 下载完成！内存占用: {len(img_bytes)} 字节 ({len(img_bytes)/1024:.1f} KB)"
        )
        return img_bytes

    def _upload_to_convert_php(
        self, image_bytes, save_path="output.bmp", bmp_w=240, bmp_h=320
    ):
        """步骤 3：把内存里的 PNG 图片打包上传给后端的 convert.php，获取标准 BMP"""
        print("🚀 3. 正在将 PNG 打包上传至 convert.php 进行云端 BMP 转码...")

        boundary = "----ESP32S3Boundary123456789"

        # 构造表单数据头
        body = []

        # 字段: format = bmp
        body.append(f"--{boundary}\r\n".encode("utf-8"))
        body.append(
            'Content-Disposition: form-data; name="format"\r\n\r\n'.encode(
                "utf-8"
            )
        )
        body.append(f"{'bmp'}\r\n".encode("utf-8"))

        # 字段: width = 240
        body.append(f"--{boundary}\r\n".encode("utf-8"))
        body.append(
            'Content-Disposition: form-data; name="width"\r\n\r\n'.encode(
                "utf-8"
            )
        )
        body.append(f"{bmp_w}\r\n".encode("utf-8"))

        # 字段: height = 320
        body.append(f"--{boundary}\r\n".encode("utf-8"))
        body.append(
            'Content-Disposition: form-data; name="height"\r\n\r\n'.encode(
                "utf-8"
            )
        )
        body.append(f"{bmp_h}\r\n".encode("utf-8"))

        # 文件字段: image = 二进制图片数据
        body.append(f"--{boundary}\r\n".encode("utf-8"))
        body.append(
            'Content-Disposition: form-data; name="image";'
            ' filename="gen.png"\r\n'.encode("utf-8")
        )
        body.append("Content-Type: image/png\r\n\r\n".encode("utf-8"))
        body.append(image_bytes)
        body.append("\r\n".encode("utf-8"))

        # 结束符
        body.append(f"--{boundary}--\r\n".encode("utf-8"))

        # 拼接完整的 payload
        payload = b"".join(body)

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": self.ua,
        }

        gc.collect()
        resp = urequests.post(
            self.convert_url, headers=headers, data=payload
        )

        if resp.status_code != 200:
            err_msg = resp.text
            resp.close()
            print("❌ convert.php 返回错误:", err_msg[:200])
            raise RuntimeError(f"convert.php 请求失败: {resp.status_code}")

        # 后端 convert.php 返回的是包含 ok 和 url 的 JSON
        res_json = resp.json()
        resp.close()
        gc.collect()

        if not res_json.get("ok") or not res_json.get("url"):
            raise RuntimeError(f"convert.php 转码失败: {res_json}")

        bmp_download_url = res_json["url"]
        print("🔗 转码成功！拿到 BMP 结果直链:", bmp_download_url[:60] + "...")

        # 步骤 4：把转好的 BMP 文件下载保存到 16MB Flash 硬盘
        print("📥 4. 正在下载最终的 BMP 文件...")
        bmp_resp = urequests.get(
            bmp_download_url, headers={"User-Agent": self.ua}, stream=True
        )

        if bmp_resp.status_code != 200:
            bmp_resp.close()
            raise RuntimeError("下载 BMP 结果失败")

        first_chunk = bmp_resp.raw.read(1024)
        if not first_chunk or not first_chunk.startswith(b"BM"):
            bmp_resp.close()
            raise RuntimeError("后端返回的文件头不是标准 'BM' 格式！")

        print("✅ BMP 头部校验成功 ('BM')！写入本地文件...")

        with open(save_path, "wb") as f:
            f.write(first_chunk)
            while True:
                chunk = bmp_resp.raw.read(1024)
                if not chunk:
                    break
                f.write(chunk)

        bmp_resp.close()
        gc.collect()
        return save_path

    def generate_image(self, prompt, save_bmp_path="output.bmp"):
        # 步骤 1: 拿到生图 URL
        png_url = self._generate_png_url(prompt)
        # 步骤 2: 下载 PNG 数据到 8MB RAM
        png_bytes = self._download_png_bytes(png_url)
        # 步骤 3 & 4: 上传转码并下载保存为标准 BMP
        return self._upload_to_convert_php(png_bytes, save_bmp_path)


def run_test():
    prompt = "我要画一个猪"
    bmp_path = "output.bmp"

    print("\n==============================================")
    print("🚀 开始单文件测试：ESP32-S3 全流程 (生图->下载->上传转码->保存)")
    print("==============================================")

    t_start = time.ticks_ms()

    try:
        client = AIBMPClient()
        saved_file = client.generate_image(prompt, save_bmp_path=bmp_path)

        t_used = time.ticks_diff(time.ticks_ms(), t_start) / 1000.0
        file_size = os.stat(saved_file)[6]

        print("\n==============================================")
        print("✨ 测试完美成功！")
        print(f"📁 文件保存到: {saved_file}")
        print(f"📊 文件大小: {file_size} 字节 ({file_size/1024:.1f} KB)")
        print(f"⏱️ 总耗时: {t_used:.2f} 秒")
        print("==============================================")

    except Exception as e:
        print("\n==============================================")
        print("❌ 测试失败，捕获到异常:")
        print(e)
        print("==============================================")
    finally:
        gc.collect()


if __name__ == "__main__":
    run_test()