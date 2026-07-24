using System;
using System.Threading;

namespace Kzq_modbus
{
    /// <summary>
    /// 线程安全共享寄存器缓存
    /// ModbusRTU采集服务写入；ModbusTcp从站读取
    /// </summary>
    public class SharedModbusData
    {
        private readonly object _lock = new();
        private ushort[] _holdingRegisters;
        public DateTime LastUpdateTime { get; private set; }

        // 初始化33个寄存器（地址100~132）
        public SharedModbusData(int regCount)
        {
            _holdingRegisters = new ushort[regCount];
        }

        /// <summary>
        /// 更新寄存器数组（RTU采集线程调用）
        /// </summary>
        public void UpdateRegisters(ushort[] source)
        {
            lock (_lock)
            {
                Array.Copy(source, _holdingRegisters, Math.Min(source.Length, _holdingRegisters.Length));
                LastUpdateTime = DateTime.Now;
            }
        }

        /// <summary>
        /// 获取寄存器副本（TCP从站响应查询使用）
        /// </summary>
        public ushort[] GetRegisters()
        {
            lock (_lock)
            {
                ushort[] copy = new ushort[_holdingRegisters.Length];
                Array.Copy(_holdingRegisters, copy, copy.Length);
                return copy;
            }
        }
    }
}