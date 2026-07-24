using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Modbus.Data;
using Modbus.Device;
using System;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;

namespace Kzq_modbus
{
    public class ModbusTcpSlaveService : BackgroundService
    {
        private readonly ILogger<ModbusTcpSlaveService> _logger;
        private readonly IConfiguration _config;
        private readonly SharedModbusData _sharedData;

        private ModbusTcpSlave _slave;
        private Task _listenTask;
        private CancellationTokenSource _slaveCts;

        private IPAddress _listenIp;
        private int _listenPort;
        private byte _slaveId;
        private ushort _baseAddress;

        public ModbusTcpSlaveService(ILogger<ModbusTcpSlaveService> logger,
            IConfiguration config,
            SharedModbusData sharedData)
        {
            _logger = logger;
            _config = config;
            _sharedData = sharedData;

            var ipStr = _config["ModbusTcpSlave:ListenIp"] ?? "0.0.0.0";
            _listenPort = int.Parse(_config["ModbusTcpSlave:Port"] ?? "502");
            _slaveId = byte.Parse(_config["ModbusTcpSlave:SlaveId"] ?? "1");
            _baseAddress = ushort.Parse(_config["ModbusTcpSlave:RegisterStartAddress"] ?? "100");

            _listenIp = IPAddress.Parse(ipStr);
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            _logger.LogInformation($"ModbusTCP从站后台服务启动，监听 {_listenIp}:{_listenPort} 从站ID:{_slaveId}");

            // 启动Modbus从站监听
            StartSlave();

            // 主循环：持续把共享缓存的最新电表数据同步到Slave寄存器
            while (!stoppingToken.IsCancellationRequested)
            {
                try
                {
                    SyncRegisterDataToSlave();
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "同步寄存器数据到ModbusTCP从站失败");
                }

                await Task.Delay(1000, stoppingToken);
            }

            StopSlave();
            _logger.LogInformation("ModbusTCP从站服务已停止");
        }

        /// <summary>
        /// 启动TCP从站
        /// </summary>
        private void StartSlave()
        {
            StopSlave();

            _slaveCts = new CancellationTokenSource();

            // 创建TcpListener
            var listener = new TcpListener(_listenIp, _listenPort);
            _slave = ModbusTcpSlave.CreateTcp(_slaveId, listener);

            // 创建寄存器存储器
            _slave.DataStore = DataStoreFactory.CreateDefaultDataStore();
            // 扩容保持寄存器到 0~132 一共133个
            int maxNeedAddr = 132;
            while (_slave.DataStore.HoldingRegisters.Count <= maxNeedAddr)
            {
                _slave.DataStore.HoldingRegisters.Add(0);
            }

            // Listen()是阻塞方法，新开线程运行
            _listenTask = Task.Run(() =>
            {
                try
                {
                    _logger.LogInformation("ModbusTCP Slave 开始监听，等待网关连接");
                    _slave.Listen();
                }
                catch (OperationCanceledException)
                {
                    // 正常关闭，不打印错误
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Modbus从站监听线程异常");
                }
            }, _slaveCts.Token);
        }

        /// <summary>
        /// 把SharedModbusData里最新寄存器，同步到Modbus从站的保持寄存器
        /// //每天早上主动往货架上补货（每秒刷新货架商品）
        /// </summary>
        private void SyncRegisterDataToSlave()
        {
            // 如果从站对象没创建，直接退出，避免空报错
            if (_slave == null) return;

            // 从共享内存拿到电表最新采集到的33个寄存器数组（副本，线程安全）
            ushort[] sourceRegs = _sharedData.GetRegisters();

            //// 获取Modbus从站内部的【保持寄存器仓库】
            var holdingStore = _slave.DataStore.HoldingRegisters;

            // 循环把电表寄存器，搬运到Modbus从站仓库
            for (int i = 0; i < sourceRegs.Length; i++)
            {
                ushort slaveRegisterAddress = (ushort)(_baseAddress + i);
                // 增加边界判断！防止寄存器长度不够导致崩溃
                if (slaveRegisterAddress < holdingStore.Count)
                {
                    holdingStore[slaveRegisterAddress] = sourceRegs[i];
                }
                else
                {
                    _logger.LogWarning($"寄存器地址{slaveRegisterAddress}超出DataStore范围");
                }
            }
        }

        /// <summary>
        /// 停止并释放从站资源
        /// </summary>
        private void StopSlave()
        {
            if (_slave != null)
            {
                try
                {
                    _slave.Dispose();
                }
                catch
                {
                }
                _slave = null;
            }
            _slaveCts?.Cancel();
            _slaveCts?.Dispose();
            _listenTask = null;
        }

        public override async Task StopAsync(CancellationToken cancellationToken)
        {
            StopSlave();
            await base.StopAsync(cancellationToken);
        }
    }
}