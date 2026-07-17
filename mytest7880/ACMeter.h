#ifndef AC_METER_H
#define AC_METER_H

#include <Arduino.h>

// ===================== 硬件配置宏（统一修改）=====================
constexpr float ADC_VREF    = 3.30f;    // ADC参考电压
constexpr uint16_t ADC_BITS   = 4096;     // 12位ADC分辨率
constexpr uint16_t SAMPLE_MS  = 20;       // 单周期采样时长(50Hz工频1周期)
constexpr int ADC_LIMIT     = 2047;     // ADC中点±最大值
// ==============================================================

class ACMeter
{
private:
    uint8_t  _pin;                      // ADC采样引脚
    uint16_t _offset_adc;               // 空载直流中点偏移
    float    _calibration_coeff;        // 综合换算系数
    float    _noise_threshold;          // ADC噪声阈值(低于则判定无信号)
    uint16_t _last_raw_adc;             // 最新单次ADC原始值

    // 滑动平均滤波
    float* _filter_buf;
    int    _win_size;
    int    _buf_idx;
    bool   _buf_full;

    // 禁用拷贝构造/赋值，防止堆内存双重释放
    ACMeter(const ACMeter&) = delete;
    ACMeter& operator=(const ACMeter&) = delete;

    // 私有基础构造，供静态工厂调用
    ACMeter(uint8_t pin, uint16_t offset, float cal, float noise, int win);

public:
    // ===================== 静态工厂：区分电压/电流，不会传错参数 =====================
    /// @brief 电压互感器实例（无采样电阻）
    /// @param pin ADC引脚
    /// @param offset 空载中点ADC值
    /// @param opGain 运放放大倍数 (设备电压变比)
    /// @param vtRatio 电压互感器变比(二次/一次)
    /// @param noiseThr 噪声阈值
    /// @param filterWin 滑动平均窗口大小
    static ACMeter CreateVoltMeter(uint8_t pin,
                                   uint16_t offset,
                                   float opGain,
                                   float vtRatio,
                                   float noiseThr,
                                   int filterWin = 40);

    /// @brief 电流互感器实例(支持双变比配置)
    /// @param pin ADC引脚
    /// @param offset 空载中点ADC值
    /// @param deviceRatio 板载设备采集变比 (如运放本身的放大倍数，无放大传 1.0f)
    /// @param extCtRatio 外部互感器物理变比 (如 100A/5A 互感器传 20.0f)
    /// @param shuntR 板载采样电阻阻值 (单位：欧姆 Ω)
    /// @param noiseThr 噪声阈值
    /// @param filterWin 滑动平均窗口大小
    static ACMeter CreateAmpMeter(uint8_t pin,
                                  uint16_t offset,
                                  float deviceRatio,
                                  float extCtRatio,
                                  float shuntR,
                                  float noiseThr,
                                  int filterWin = 40);

    // 析构：安全释放堆内存
    ~ACMeter();

    // ===================== 功能接口 =====================
    void UpdateSampleBlock();
    void ClearFilter();
    void CalibrateZero(uint16_t sampleCnt = 100);
    float GetFilterValue() const;
    float GetInstantValue() const;
    uint16_t GetRawADC() const;
    void SetOffset(uint16_t newOffset);
    uint16_t GetOffset() const;
};

// ===================== 函数实现 =====================
inline ACMeter::ACMeter(uint8_t pin, uint16_t offset, float cal, float noise, int win)
{
    _pin = pin;
    pinMode(_pin, INPUT_ANALOG);

    _offset_adc = offset;
    _calibration_coeff = cal;
    _noise_threshold = noise;
    _win_size = win;
    _last_raw_adc = 0;

    _buf_idx = 0;
    _buf_full = false;
    _filter_buf = new float[_win_size];

    for (int i = 0; i < _win_size; i++)
        _filter_buf[i] = 0.0f;
}

inline ACMeter ACMeter::CreateVoltMeter(uint8_t pin, uint16_t offset, float opGain, float vtRatio, float noiseThr, int filterWin)
{
    float cal = opGain * vtRatio;
    return ACMeter(pin, offset, cal, noiseThr, filterWin);
}

// 【已修改】支持双变比的电流工厂函数实现
inline ACMeter ACMeter::CreateAmpMeter(uint8_t pin, uint16_t offset, float deviceRatio, float extCtRatio, float shuntR, float noiseThr, int filterWin)
{
    // 电流综合计算公式：
    // 真实电流 = (ADC引脚电压 / 采样电阻) * 外部CT变比 * 板载设备变比
    float cal = (extCtRatio / shuntR) * deviceRatio;
    return ACMeter(pin, offset, cal, noiseThr, filterWin);
}

inline ACMeter::~ACMeter()
{
    if (_filter_buf != nullptr)
    {
        delete[] _filter_buf;
        _filter_buf = nullptr;
    }
}

inline void ACMeter::UpdateSampleBlock()
{
    int64_t sumSquare = 0;
    uint32_t sampleCnt = 0;
    uint32_t startMs = millis();

    while (millis() - startMs < SAMPLE_MS)
    {
        uint16_t raw = analogRead(_pin);
        _last_raw_adc = raw;

        int16_t acRaw = static_cast<int16_t>(raw) - static_cast<int16_t>(_offset_adc);
        if (acRaw > ADC_LIMIT) acRaw = ADC_LIMIT;
        if (acRaw < -ADC_LIMIT) acRaw = -ADC_LIMIT;

        sumSquare += static_cast<int64_t>(acRaw) * acRaw;
        sampleCnt++;
    }

    float instant = 0.0f;
    if (sampleCnt > 0)
    {
        float rmsAdc = sqrtf(static_cast<float>(sumSquare) / sampleCnt);
        if (rmsAdc < _noise_threshold)
        {
            instant = 0.0f;
        }
        else
        {
            float pinVolt = (rmsAdc * ADC_VREF) / static_cast<float>(ADC_BITS);
            instant = pinVolt * _calibration_coeff;
        }
    }

    _filter_buf[_buf_idx] = instant;
    _buf_idx++;
    if (_buf_idx >= _win_size)
    {
        _buf_idx = 0;
        _buf_full = true;
    }
}

inline void ACMeter::ClearFilter()
{
    _buf_idx = 0;
    _buf_full = false;
    for (int i = 0; i < _win_size; i++)
        _filter_buf[i] = 0.0f;
}

inline void ACMeter::CalibrateZero(uint16_t sampleCnt)
{
    uint32_t sum = 0;
    for (uint16_t i = 0; i < sampleCnt; i++)
    {
        sum += analogRead(_pin);
        delay(1);
    }
    _offset_adc = static_cast<uint16_t>(sum / sampleCnt);
    ClearFilter();
}

inline float ACMeter::GetFilterValue() const
{
    int validCnt = _buf_full ? _win_size : _buf_idx;
    if (validCnt == 0) return 0.0f;

    float sum = 0.0f;
    for (int i = 0; i < validCnt; i++)
        sum += _filter_buf[i];
    return sum / static_cast<float>(validCnt);
}

inline float ACMeter::GetInstantValue() const
{
    int idx = _buf_idx - 1;
    if (idx < 0) idx = _win_size - 1;
    return _filter_buf[idx];
}

inline uint16_t ACMeter::GetRawADC() const
{
    return _last_raw_adc;
}

inline void ACMeter::SetOffset(uint16_t newOffset)
{
    _offset_adc = newOffset;
}

inline uint16_t ACMeter::GetOffset() const
{
    return _offset_adc;
}

#endif