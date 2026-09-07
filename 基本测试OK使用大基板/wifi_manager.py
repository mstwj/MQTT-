import network
import socket
import time
import os
import machine

# WiFi常量配置
AP_SSID = "ESP32-Recorder"
AP_PWD = ""
WIFI_CFG_FILE = "wifi.cfg"

sta_wlan = network.WLAN(network.STA_IF)
ap_wlan = network.WLAN(network.AP_IF)


def load_wifi_config():
    """读取保存的WiFi账号密码"""
    try:
        with open(WIFI_CFG_FILE, "r") as f:
            ssid = f.readline().strip()
            pwd = f.readline().strip()
            return ssid, pwd
    except OSError:
        return None, None


def save_wifi_config(ssid, pwd):
    """保存WiFi账号密码到文件"""
    with open(WIFI_CFG_FILE, "w") as f:
        f.write(f"{ssid}\n{pwd}\n")


def connect_router_wifi(ssid, pwd, ui_callback=None):
    """STA连接路由器WiFi

    ui_callback(text1, text2): 界面刷新回调函数，如果为 None 则自动使用 print 打印
    返回：(成功标志, ip地址)
    """

    # 内部辅助函数：统一处理 UI 回调或控制台打印
    def notify(title, msg):
        if ui_callback:
            ui_callback(title, msg)
        else:
            print(f"[{title}] {msg}")

    sta_wlan.active(True)
    if sta_wlan.isconnected():
        ip = sta_wlan.ifconfig()[0]
        return True, ip

    notify("Connect WIFI...", ssid)
    try:
        sta_wlan.connect(ssid, pwd)
    except OSError:
        pass

    wait = 0
    while not sta_wlan.isconnected() and wait < 40:
        time.sleep(0.5)
        wait += 1

    if sta_wlan.isconnected():
        ip = sta_wlan.ifconfig()[0]
        notify("WIFI OK", f"IP:{ip}")
        return True, ip
    else:
        sta_wlan.disconnect()
        sta_wlan.active(False)
        notify("WIFI Connect Fail", "Enter AP Mode")
        return False, None
    
def start_ap_web_server(ui_callback):
    """开启AP热点 + Web配网服务，阻塞运行"""
    sta_wlan.active(False)
    ap_wlan.active(True)
    ap_wlan.config(essid=AP_SSID, password=AP_PWD)
    print(f"热点开启：{AP_SSID}，访问 192.168.4.1")

    html_page = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>ESP32 WIFI配置</title>
        <meta name="viewport" content="width=device-width,initial-scale=1">
    </head>
    <body>
        <h3>WiFi参数设置</h3>
        <form action="/save" method="post">
            SSID:<br>
            <input type="text" name="ssid"><br><br>
            PASSWORD:<br>
            <input type="text" name="pwd"><br><br>
            <input type="submit" value="保存并重启">
        </form>
    </body>
    </html>
    """

    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    ui_callback("AP MODE", "192.168.4.1")

    while True:
        conn, addr = s.accept()
        req = conn.recv(1024).decode()
        if "POST /save" in req:
            try:
                body = req.split("\r\n\r\n")[1]
                params = dict(x.split("=") for x in body.split("&"))
                new_ssid = params["ssid"]
                new_pwd = params["pwd"]
                save_wifi_config(new_ssid, new_pwd)

                resp = """HTTP/1.1 200 OK
Content-Type: text/html

<h3>保存成功！设备即将重启接入WiFi</h3>
<script>setTimeout(()=>{window.location.reload()},3000)</script>
"""
                conn.send(resp)
                conn.close()
                time.sleep(1.5)
                s.close()
                machine.reset()
            except Exception as e:
                conn.send("HTTP/1.1 200 OK\n\n参数错误！")
        else:
            conn.send(f"HTTP/1.1 200 OK\nContent-Type:text/html\n\n{html_page}")
        conn.close()


def is_sta_connected():
    return sta_wlan.isconnected()


def get_ip():
    if sta_wlan.isconnected():
        return sta_wlan.ifconfig()[0]
    return None