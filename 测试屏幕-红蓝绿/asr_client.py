import gc
import os
import ujson as json
import usocket as socket

# 尝试导入 SSL 库 (兼容新旧 MicroPython 固件)
try:
    import ssl
except ImportError:
    import ussl as ssl

SILICONFLOW_KEY = "sk-lisenkrkcvdlmmavgytlsnpwpodcfyqrmnszopgzwpwespbe"  # 换成你的 Key
HOST = "api.siliconflow.cn"
PORT = 443
PATH = "/v1/audio/transcriptions"
MODEL_NAME = "FunAudioLLM/SenseVoiceSmall"  # 硅基流动上的极速语音识别模型


def transcribe_wav(filename="record.wav"):
    # 手动触发垃圾回收，释放出最大内存给 SSL 握手
    gc.collect()

    try:
        file_size = os.stat(filename)[6]
        print(f"📡 正在上传 {filename} ({file_size} 字节) 进行语音识别...")
    except Exception as e:
        return f"Error: 文件不存在 - {e}"

    boundary = "----ESP32Boundary7MA4YWxkTrZu0gW"

    header_data = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: audio/wav\r\n\r\n"
    )

    model_data = (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f"{MODEL_NAME}\r\n"
        f"--{boundary}--\r\n"
    )

    content_length = len(header_data) + file_size + len(model_data)

    s = None
    try:
        # 1. 解析域名 IP
        addr_info = socket.getaddrinfo(HOST, PORT)
        addr = addr_info[0][-1]

        # 2. 创建原生 Socket
        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_sock.settimeout(15)  # 设置 15 秒超时
        raw_sock.connect(addr)

        # 3. 进行 SSL/TLS 包装
        if hasattr(ssl, "wrap_socket"):
            s = ssl.wrap_socket(raw_sock, server_hostname=HOST)
        else:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.verify_mode = ssl.CERT_NONE
            s = ctx.wrap_socket(raw_sock, server_hostname=HOST)

        # 4. 发送 HTTP 请求头
        http_headers = (
            f"POST {PATH} HTTP/1.1\r\n"
            f"Host: {HOST}\r\n"
            f"Authorization: Bearer {SILICONFLOW_KEY}\r\n"
            f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
            f"Content-Length: {content_length}\r\n"
            f"Connection: close\r\n\r\n"
        )
        s.write(http_headers.encode("utf-8"))

        # 5. 发送 Multipart Body（流式读取文件）
        s.write(header_data.encode("utf-8"))

        with open(filename, "rb") as f:
            buf = bytearray(2048)
            while True:
                num_read = f.readinto(buf)
                if num_read <= 0:
                    break
                s.write(buf[:num_read])

        s.write(model_data.encode("utf-8"))

        # 6. 读取响应结果
        response = s.read()
        if not response:
            return "Error: 服务器未返回数据"

        response_str = response.decode("utf-8")

        # 寻找 JSON 体的起始位置
        json_start = response_str.find("{")
        if json_start != -1:
            res_json = json.loads(response_str[json_start:])
            # 获取识别出来的文本
            text = res_json.get("text", "")
            return text.strip()
        else:
            return f"Error: 响应格式异常 - {response_str[:100]}"

    except Exception as e:
        print("ASR 详细错误:", e)
        return f"Error: {str(e)}"
    finally:
        if s:
            s.close()
        gc.collect()  # 再次清理内存