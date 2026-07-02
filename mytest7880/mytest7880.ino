#include <Arduino.h>
#include "ACMeter.h" 

HardwareSerial Serial1(PA10, PA9);

// ==================== 🛠️ 参数配置 (已同步工程师要求的 2.41V 偏置) ====================

// 1. 电压通道 (固定偏置 3228)
// 第一个是 引脚..  第2个是 偏移值  第3个 硬件工程师知道.. 第4个 互感器变比.. 第5个 (电压没用,电流可以)  第6个 门限值..
ACMeter voltageMeter(PA4, 3228, 654.64f, 1.0f, 1.0f, 60.0f);

// 2. 电流通道 (固定偏置 2991 对应 2.41V)
ACMeter currentMeter(PA5, 2991, 6.3927f, 20.0f, 1.0f, 15.0f);

// ==============================================================================


void setup() {
    Serial1.begin(115200);
    delay(500);

    #if defined(ARDUINO_ARCH_STM32)
        analogReadResolution(12); // STM32 开启 12 位 ADC 采样
    #endif

    Serial1.println("\r\n================== 调试模式启动 ==================");
    Serial1.print("--> 电压固定偏置: "); Serial1.println(voltageMeter.getOffset());
    Serial1.print("--> 电流固定偏置 (2.41V): "); Serial1.println(currentMeter.getOffset());
    Serial1.println("==================================================");
}

void loop() {
    // 1. 执行周期采样
    voltageMeter.updateSample();
    currentMeter.updateSample();

    // 2. 获取最终计算出的有效值结果（市电电压和实际总电流）
    float final_voltage = voltageMeter.getFilteredValue();
    float final_current = currentMeter.getFilteredValue();

    // 3. 获取单片机引脚当前最后一次读到的原始 ADC 裸数据
    uint16_t volt_raw_adc = voltageMeter.getRawADC();
    uint16_t curr_raw_adc = currentMeter.getRawADC();

    // 4. 将 ADC 字数直接换算成引脚上的 10 进制原始电压值 (0V ~ 3.3V)
    float volt_pin_voltage = ((float)volt_raw_adc * 3.3f) / 4096.0f;
    float curr_pin_voltage = ((float)curr_raw_adc * 3.3f) / 4096.0f;

    // 5. 串口清晰输出
    Serial1.print("V: "); Serial1.print(final_voltage, 1); Serial1.print("V");
    Serial1.print(" (PinVolt: "); Serial1.print(volt_pin_voltage, 3); Serial1.print("V)");
    
    Serial1.print("  |  I: "); Serial1.print(final_current, 3); Serial1.print("A");
    Serial1.print(" (PinVolt: "); Serial1.print(curr_pin_voltage, 3); Serial1.println("V)");

    delay(300); // 刷新间隔
}