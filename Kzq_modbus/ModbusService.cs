using Kzq_modbus.Data;
using Kzq_modbus.Models;
using Modbus.Device;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO.Ports;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace Kzq_modbus
{
    public class ModbusService : BackgroundService
    {
        private readonly ILogger<ModbusService> _logger;
        private readonly IServiceScopeFactory _scopeFactory;
        private readonly IConfiguration _config;
        private ModbusSerialMaster _modbusMaster;
        private SerialPort _serialPort;

        private readonly SharedModbusData _sharedData;

        #region Modbus RTU配置
        private string ComPort => _config["ModbusRtu:ComPort"] ?? "COM3";
        private int BaudRate => int.Parse(_config["ModbusRtu:BaudRate"] ?? "9600");
        private Parity Parity => Enum.Parse<Parity>(_config["ModbusRtu:Parity"] ?? "None");
        private int DataBits => int.Parse(_config["ModbusRtu:DataBits"] ?? "8");
        private StopBits StopBits => Enum.Parse<StopBits>(_config["ModbusRtu:StopBits"] ?? "One");
        private byte SlaveId => byte.Parse(_config["ModbusRtu:SlaveId"] ?? "1");
        #endregion

        
        public ModbusService(ILogger<ModbusService> logger,
                                 IServiceScopeFactory scopeFactory,
                                 IConfiguration config,
                                 SharedModbusData sharedData)
        {
            _logger = logger;
            _scopeFactory = scopeFactory;
            _config = config;
            _sharedData = sharedData;
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            _logger.LogInformation("MODBUS RTU后台服务正在启动...");

            while (!stoppingToken.IsCancellationRequested)
            {
                try
                {
                    if (_serialPort == null || !_serialPort.IsOpen || _modbusMaster == null)
                    {
                        await ConnectModbusRtuAsync(stoppingToken);
                    }

                    await ModbusReadWriteTask(stoppingToken);

                    await Task.Delay(5000, stoppingToken);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "串口主循环异常");
                    await Task.Delay(5000, stoppingToken);
                }
                await Task.Delay(1000, stoppingToken);
            }
        }

        private async Task ConnectModbusRtuAsync(CancellationToken token)
        {
            await Task.Run(() =>
            {
                _logger.LogInformation($"正在打开串口 {ComPort} 波特率:{BaudRate} 从站ID:{SlaveId}");
                _serialPort = new SerialPort(ComPort, BaudRate, Parity, DataBits, StopBits);
                _serialPort.ReadTimeout = 3000;
                _serialPort.WriteTimeout = 3000;
                _serialPort.Open();
                _modbusMaster = ModbusSerialMaster.CreateRtu(_serialPort);
            }, token);

            _logger.LogInformation("Modbus RTU 串口连接成功！");
        }

        private async Task ModbusReadWriteTask(CancellationToken token)
        {
            ushort[] holdingRegs = null;
            try
            {
                holdingRegs = await Task.Run(() =>
                {
                    return _modbusMaster.ReadHoldingRegisters(SlaveId, startAddress: 100, numberOfPoints: 33);
                }, token);
                _logger.LogDebug("Modbus寄存器读取成功");

                // =====新增这一行！把最新寄存器推入共享缓存，TCP从站可以对外提供=====
                _sharedData.UpdateRegisters(holdingRegs);

            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Modbus读取寄存器失败");
                return;
            }

            // ========= 原始寄存器值 =========
            int va = holdingRegs[0];
            int ia = holdingRegs[1];
            int p_a = holdingRegs[2];
            int q_a = holdingRegs[3];
            int s_a = holdingRegs[4];
            int pf_a = holdingRegs[5];
            int thdv_a = holdingRegs[6];
            int thidi_a = holdingRegs[7];

            int vb = holdingRegs[8];
            int ib = holdingRegs[9];
            int p_b = holdingRegs[10];
            int q_b = holdingRegs[11];
            int s_b = holdingRegs[12];
            int pf_b = holdingRegs[13];
            int thdv_b = holdingRegs[14];
            int thidi_b = holdingRegs[15];

            int vc = holdingRegs[16];
            int ic = holdingRegs[17];
            int p_c = holdingRegs[18];
            int q_c = holdingRegs[19];
            int s_c = holdingRegs[20];
            int pf_c = holdingRegs[21];
            int thdv_c = holdingRegs[22];
            int thidi_c = holdingRegs[23];

            int p_total = holdingRegs[24];
            int q_total = holdingRegs[25];
            int pf_total = holdingRegs[27];
            int thdv_total = holdingRegs[28];
            int thdi_total = holdingRegs[29];

            // ========= 构建JSON传输实体（两种方案：传原始放大整数 / 传换算后浮点数，你任选）=========
            var sendData = new
            {
                Timestamp = DateTime.Now,
                Raw = new
                {
                    va,
                    ia,
                    p_a,
                    q_a,
                    s_a,
                    pf_a,
                    thdv_a,
                    thidi_a,
                    vb,
                    ib,
                    p_b,
                    q_b,
                    s_b,
                    pf_b,
                    thdv_b,
                    thidi_b,
                    vc,
                    ic,
                    p_c,
                    q_c,
                    s_c,
                    pf_c,
                    thdv_c,
                    thidi_c,
                    p_total,
                    q_total,
                    pf_total,
                    thdv_total,
                    thdi_total
                },
                RealValue = new
                {
                    A相电压 = va / 10.0,
                    A相电流 = ia / 10.0,
                    A相有功 = p_a / 10.0,
                    A相无功 = q_a / 10.0,
                    A相视在 = s_a / 10.0,
                    A相PF = pf_a / 100.0,

                    B相电压 = vb / 10.0,
                    B相电流 = ib / 10.0,
                    B相有功 = p_b / 10.0,
                    B相无功 = q_b / 10.0,
                    B相视在 = s_b / 10.0,
                    B相PF = pf_b / 100.0,

                    C相电压 = vc / 10.0,
                    C相电流 = ic / 10.0,
                    C相有功 = p_c / 10.0,
                    C相无功 = q_c / 10.0,
                    C相视在 = s_c / 10.0,
                    C相PF = pf_c / 100.0,

                    总有功 = p_total / 10.0,
                    总无功 = q_total / 10.0,
                    总PF = pf_total / 100.0
                }
            };

            try
            {
                using (var scope = _scopeFactory.CreateScope())
                {
                    var dbContext = scope.ServiceProvider.GetRequiredService<AppDbContext>();

                    var dataModel = new tw_kzq
                    {
                        va = va,
                        vb = vb,
                        vc = vc,
                        ia = ia,
                        ib = ib,
                        ic = ic,

                        p_a = p_a,
                        p_b = p_b,
                        p_c = p_c,

                        q_a = q_a,
                        q_b = q_b,
                        q_c = q_c,

                        s_a = s_a,
                        s_b = s_b,
                        s_c = s_c,

                        pf_a = pf_a,
                        pf_b = pf_b,
                        pf_c = pf_c,

                        thdv_a = thdv_a,
                        thdv_b = thdv_b,
                        thdv_c = thdv_c,

                        thidi_a = thidi_a,
                        thidi_b = thidi_b,
                        thidi_c = thidi_c,

                        p_total = p_total,
                        q_total = q_total,
                        pf_total = pf_total,
                        thdv_total = thdv_total,
                        thdi_total = thdi_total,

                        create_time = DateTime.Now
                    };

                    dbContext.twj_kzqs.Add(dataModel);
                    await dbContext.SaveChangesAsync(token);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "电表数据写入数据库失败");
            }
        }


        // 服务停止时释放串口资源
        public override async Task StopAsync(CancellationToken cancellationToken)
        {
            _logger.LogInformation("Modbus服务正在停止，关闭串口...");
            _modbusMaster?.Dispose();
            if (_serialPort != null && _serialPort.IsOpen)
                _serialPort.Close();
            _serialPort?.Dispose();
            await base.StopAsync(cancellationToken);
        }
    }
}