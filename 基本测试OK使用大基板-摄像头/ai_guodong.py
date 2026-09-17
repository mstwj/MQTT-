import socket
import ssl


def send_bmp_to_ai(file_path="photo.bmp", prompt="原图显示", ui_callback=None):
    """
    发送 BMP 到 AI 服务器，并通过 ui_callback 实时更新 LCD UI 提示
    :param ui_callback: 外部传入的显示函数，例: lambda title, msg: ui.render(title, msg)
    """
    host = "www.passnow.tech"
    port = 443  # HTTPS 端口
    path = "/img.php"
    boundary = "----ESP32S3Boundary7MA4YWxkTrZu0gW"

    # 辅助更新 UI 函数
    def update_ui(title, msg):
        if ui_callback:
            try:
                ui_callback(title, msg)
            except Exception:
                pass

    # 1. 读取本地 BMP 文件
    update_ui("AI 重绘", "📂 读取本地图片...")
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
    except Exception as e:
        print(f"❌ 读取本地文件失败: {e}")
        update_ui("错误", "❌ 读取本地图片失败")
        return None

    # 2. 构建 multipart/form-data 数据包
    body_parts = []

    # 字段 1: prompt
    body_parts.append(f"--{boundary}\r\n".encode("utf-8"))
    body_parts.append(
        f'Content-Disposition: form-data; name="prompt"\r\n\r\n{prompt}\r\n'.encode(
            "utf-8"
        )
    )

    # 字段 2: raw=1
    body_parts.append(f"--{boundary}\r\n".encode("utf-8"))
    body_parts.append(
        b'Content-Disposition: form-data; name="raw"\r\n\r\n1\r\n'
    )

    # 字段 3: image (photo.bmp)
    body_parts.append(f"--{boundary}\r\n".encode("utf-8"))
    body_parts.append(
        b'Content-Disposition: form-data; name="image";'
        b' filename="photo.bmp"\r\n'
    )
    body_parts.append(b"Content-Type: image/bmp\r\n\r\n")
    body_parts.append(file_bytes)
    body_parts.append(b"\r\n")

    body_parts.append(f"--{boundary}--\r\n".encode("utf-8"))

    full_body = b"".join(body_parts)

    # 3. 构建 HTTP/1.1 请求头
    header = (
        f"POST {path} HTTP/1.1\r\n"
        + f"Host: {host}\r\n"
        + f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
        + f"Content-Length: {len(full_body)}\r\n"
        + "Connection: close\r\n\r\n"
    )

    # 4. 建立 HTTPS 连接与数据收发
    print("正在上传 photo.bmp 到 AI 服务器...")
    update_ui("AI 重绘 (1/4)", "🌐 正在连接服务器...")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(60)  # 放宽超时时间以适应图生图推理
        s.connect((host, port))
        s = ssl.wrap_socket(s)  # SSL 加密

        # 🌟 UI 进度提示 1：正在上传图片
        update_ui("AI 重绘 (2/4)", "📤 正在上传图片数据...")
        s.write(header.encode("utf-8"))
        s.write(full_body)

        # 🌟 UI 进度提示 2：上传完成，等待 AI 生成（最耗时节点）
        update_ui("AI 重绘 (3/4)", "🤖 AI 正在分析与生成\n(请稍候 10-15s)...")

        response_data = b""
        received_first_chunk = False

        while True:
            try:
                chunk = s.read(2048)
                if not chunk:
                    break

                # 🌟 UI 进度提示 3：接收到第一个数据包，说明 AI 生成完毕，正在传输回包
                if not received_first_chunk:
                    received_first_chunk = True
                    update_ui("AI 重绘 (4/4)", "📥 正在下载 AI 效果图...")

                response_data += chunk
            except Exception:
                break
        s.close()

        # 5. 解析 HTTP 响应，分离 Header 和 Body
        header_end = response_data.find(b"\r\n\r\n")
        if header_end != -1:
            img_bytes = response_data[header_end + 4 :]
            print(
                f"上传成功！收到 AI 处理后的 BMP 数据，大小: {len(img_bytes)} 字节"
            )

            # 🌟 UI 进度提示 4：保存与渲染
            update_ui("AI 重绘", "💾 保存图片中...")

            # 保存为 result.bmp
            with open("result.bmp", "wb") as f:
                f.write(img_bytes)
            print("已成功保存为 result.bmp")
            return img_bytes
        else:
            print("❌ 服务器响应解析失败")
            update_ui("错误", "❌ 解析服务器响应失败")
            return None

    except Exception as e:
        print(f"❌ 网络请求异常: {e}")
        update_ui("错误", "❌ 网络连接或超时")
        return None