import binascii
import socket
import ujson


def send_bmp_to_ai(file_path="photo.bmp", prompt="把照片的头发搞成黄色"):
    """直接将 Flash 中的 photo.bmp 上传至 http://www.passnow.tech/img.php

    获取生成的图片二进制流/URL
    """
    host = "www.passnow.tech"
    port = 80
    path = "/img.php"

    # 1. 读取本地 photo.bmp 文件
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    # 2. 构建 multipart/form-data 的边界字符串 (Boundary)
    boundary = "----ESP32S3Boundary7MA4YWxkTrZu0gW"

    # 3. 拼装 prompt 和 image 表单项
    # 注意：这里如果加上 -F "raw=1"，服务器会直接返回图片的二进制字节数据
    body_parts = []

    # 字段 1: prompt
    body_parts.append(f"--{boundary}\r\n".encode("utf-8"))
    body_parts.append(
        b'Content-Disposition: form-data; name="prompt"\r\n\r\n'
    )
    body_parts.append(prompt.encode("utf-8"))
    body_parts.append(b"\r\n")

    # 字段 2: raw (如果想要直接拿图片二进制数据)
    body_parts.append(f"--{boundary}\r\n".encode("utf-8"))
    body_parts.append(b'Content-Disposition: form-data; name="raw"\r\n\r\n')
    body_parts.append(b"1\r\n")

    # 字段 3: image 文件数据
    body_parts.append(f"--{boundary}\r\n".encode("utf-8"))
    body_parts.append(
        b'Content-Disposition: form-data; name="image";'
        b' filename="photo.bmp"\r\n'
    )
    body_parts.append(b"Content-Type: image/bmp\r\n\r\n")
    body_parts.append(file_bytes)
    body_parts.append(b"\r\n")

    # 结束标志
    body_parts.append(f"--{boundary}--\r\n".encode("utf-8"))

    # 计算 Payload 总字节长度
    full_body = b"".join(body_parts)
    content_length = len(full_body)

    # 4. 构建 HTTP 请求头
    header = (
        f"POST {path} HTTP/1.1\r\n"
        + f"Host: {host}\r\n"
        + f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
        + f"Content-Length: {content_length}\r\n"
        + f"Connection: close\r\n\r\n"
    )

    # 5. 通过 Socket 发送请求（无论是 Wi-Fi 还是 4G AT 透传 socket 均可使用）
    print("正在上传 photo.bmp 到 AI 服务器...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.sendall(header.encode("utf-8"))
    s.sendall(full_body)

    # 6. 接收服务器返回数据
    response_data = b""
    while True:
        chunk = s.recv(1024)
        if not chunk:
            break
        response_data += chunk
    s.close()

    # 7. 分离 HTTP 响应头与 Body 内容
    header_end = response_data.find(b"\r\n\r\n")
    if header_end != -1:
        img_raw_result = response_data[header_end + 4 :]
        print("上传成功！接收到 AI 修改后的图片，大小:", len(img_raw_result), "字节")
        return img_raw_result  # 这就是返回的图片数据！可以直接保存或解码刷屏
    else:
        print("请求失败，未收到有效 HTTP 响应")
        return None
