import time
from display_ui import UIManager

# 1. 初始化 UI 管理器（会自动初始化屏幕与 SPI）
ui = UIManager()

# 常用 RGB565 颜色常量定义
RED = 0xF800
GREEN = 0x07E0
BLUE = 0x001F
WHITE = 0xFFFF
BLACK = 0x0000

print("=== 开始屏幕 RGB 色彩与 UI 功能测试 ===")

# --- 阶段 1：红、绿、蓝全屏测试 ---
# 1. 全屏纯红
ui.lcd.fill(RED)
ui.lcd.show()
print("显示：红色 (RED)")
time.sleep(1)

# 2. 全屏纯绿
ui.lcd.fill(GREEN)
ui.lcd.show()
print("显示：绿色 (GREEN)")
time.sleep(1)

# 3. 全屏纯蓝
ui.lcd.fill(BLUE)
ui.lcd.show()
print("显示：蓝色 (BLUE)")
time.sleep(1)

# --- 阶段 2：UI 文本渲染测试 ---
# 绘制带有中文标题和正文的界面
ui.render(title="系统测试", content="红绿蓝三色测试完成！\n正在测试 uFont 中文字体渲染及自动换行功能。", color=WHITE)
print("显示：界面文字测试")