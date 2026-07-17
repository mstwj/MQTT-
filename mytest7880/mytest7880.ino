#include <Arduino.h>
#include "ACMeter.h" 

HardwareSerial Serial3(PB11, PB10 );

// ==================== 🛠️ 参数配置 (工程师给定参数完全保留) ====================
// 电压通道 PC2，偏移3228，增益657.05，变比1，噪声60，滤波窗口40
ACMeter voltageMeter = ACMeter::CreateVoltMeter(
    PC2,
    2048,
    646.96f,//
    1.0f,
    0.0f,
    40
);

// 电流通道 PA1，偏移2991(2.41V)，板载设备采集变比 (原运放增益)，CT变比20，采样电阻1Ω，噪声15
ACMeter currentMeter = ACMeter::CreateAmpMeter(
    PA1, // ADC 引脚
    2048, // 【已校准】空载中点偏移 (对应 1.648V 左右)
    2000.0f, // 【参数 1】板载设备采集变比 (原运放增益)    
    20.0f, //【参数 2】外部互感器物理变比 (例如 100A/5A)
    200.0f, // 采样电阻阻值 (1Ω)
    15.0f,//5. 【修改这里！】噪声阈值：设为 15.0f (低于此 ADC 噪声波幅的直接归零)
    40
);
// ==============================================================================

void setup() {
    Serial3.begin(115200);
    delay(500);

    #if defined(ARDUINO_ARCH_STM32)
        analogReadResolution(12); // STM32 开启 12 位 ADC 采样
    #endif

    Serial3.println("\r\n================== 调试模式启动 ==================");
    Serial3.print("--> 电压固定偏置: "); Serial3.println(voltageMeter.GetOffset());
    Serial3.print("--> 电流固定偏置 (2.41V): "); Serial3.println(currentMeter.GetOffset());
    Serial3.println("==================================================");
}

void loop() {
    // 执行20ms阻塞周期采样
    voltageMeter.UpdateSampleBlock();
    currentMeter.UpdateSampleBlock();

    // 滤波后稳定有效值
    float final_voltage = voltageMeter.GetFilterValue();
    float final_current = currentMeter.GetFilterValue();

    // 原始ADC数值
    uint16_t volt_raw_adc = voltageMeter.GetRawADC();
    uint16_t curr_raw_adc = currentMeter.GetRawADC();

    // ADC转引脚实际电压 0~3.3V
    float volt_pin_voltage = ((float)volt_raw_adc * 3.3f) / 4096.0f;
    float curr_pin_voltage = ((float)curr_raw_adc * 3.3f) / 4096.0f;

    // 串口打印
    Serial3.print("V: "); Serial3.print(final_voltage, 1); Serial3.print("V");
    Serial3.print(" (PinVolt: "); Serial3.print(volt_pin_voltage, 3); Serial3.print("V)");
    
    Serial3.print("  |  I: "); Serial3.print(final_current, 3); Serial3.print("A");
    Serial3.print(" (PinVolt: "); Serial3.print(curr_pin_voltage, 3); Serial3.println("V)");

    delay(300); // 刷新间隔
}