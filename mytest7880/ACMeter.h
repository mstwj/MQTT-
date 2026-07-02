#ifndef AC_METER_H
#define AC_METER_H

#include <Arduino.h>

class ACMeter {
private:
    uint8_t  _pin;               // 采样引脚
    uint16_t _offset_adc;        // 直流偏置 ADC 值
    float    _calibration;       // 综合校准系数
    float    _noise_threshold;   // 消噪门限
    uint16_t _last_raw_adc;      // 🔴【新增】记录最后一次读取的原始 ADC 裸数据

    // 滑动平均滤波缓冲区
    float* _filter_buffer;
    int      _window_size;
    int      _buffer_index;
    bool     _buffer_full;

public:
    ACMeter(uint8_t pin, uint16_t offset_adc, float hardware_g, float ratio, float sense_res, float noise_threshold, int filter_window = 40) {
        _pin = pin;
        _offset_adc = offset_adc; 
        _noise_threshold = noise_threshold;
        _window_size = filter_window;
        _last_raw_adc = 0;       // 初始化
        
        _buffer_index = 0;
        _buffer_full = false;
        _filter_buffer = new float[_window_size]{0.0f};

        if (sense_res == 1.0f) {
            _calibration = hardware_g * ratio; 
        } else {
            _calibration = (ratio / sense_res) * hardware_g;
        }
    }

    ~ACMeter() {
        delete[] _filter_buffer;
    }

    /**
     * @brief 核心采样与计算逻辑 (需要连续运行 20ms 以覆盖一个工频周期)
     */
    void updateSample() {
        int64_t sum_squared_adc = 0;
        uint32_t sample_count = 0;

        uint32_t start_time = millis();
        while ((millis() - start_time) < 20) {
            int16_t raw_adc = analogRead(_pin);
            _last_raw_adc = raw_adc; // 🔴【新增】实时记录最后一次的原始 ADC 值
            
            int16_t ac_signal = raw_adc - _offset_adc; 
            sum_squared_adc += (int32_t)ac_signal * ac_signal;
            sample_count++;
        }

        float instant_value = 0.0f;
        if (sample_count > 0) {
            float rms_adc = sqrt((float)sum_squared_adc / sample_count);

            if (rms_adc < _noise_threshold) {
                instant_value = 0.0f;
            } else {
                instant_value = ((rms_adc * 3.3f) / 4096.0f) * _calibration;
            }
        }

        _filter_buffer[_buffer_index] = instant_value;
        _buffer_index++;
        if (_buffer_index >= _window_size) {
            _buffer_index = 0;
            _buffer_full = true;
        }
    }

    /**
     * @brief 获取滤波后的平稳测量结果
     */
    float getFilteredValue() {
        float sum = 0;
        int actual_count = _buffer_full ? _window_size : _buffer_index;
        if (actual_count == 0) return 0.0f;

        for (int i = 0; i < actual_count; i++) {
            sum += _filter_buffer[i];
        }
        return sum / actual_count;
    }

    // 🔴【新增】对外暴露原始 ADC 值的接口
    uint16_t getRawADC() { return _last_raw_adc; }
    
    void setOffset(uint16_t new_offset) { _offset_adc = new_offset; }
    uint16_t getOffset() { return _offset_adc; }
};

#endif