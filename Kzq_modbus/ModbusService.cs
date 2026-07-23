using Kzq_modbus.Data;
using Kzq_modbus.Models;
using Modbus.Device;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.IO.Ports;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Kzq_modbus
{
    public class ModbusService : BackgroundService
    {
        private readonly ILogger<ModbusService> _logger;
        private readonly IServiceScopeFactory _scopeFactory; // 替换直接注入的AppDbContext
        private readonly IConfiguration _config;
        private ModbusSerialMaster _modbusMaster;
        private SerialPort _serialPort;

        // 从配置文件读取（不再写死！）
        private string ComPort => _config["ModbusRtu:ComPort"] ?? "COM3";
        private int BaudRate => int.Parse(_config["ModbusRtu:BaudRate"] ?? "9600");
        private Parity Parity => Enum.Parse<Parity>(_config["ModbusRtu:Parity"] ?? "None");
        private int DataBits => int.Parse(_config["ModbusRtu:DataBits"] ?? "8");
        private StopBits StopBits => Enum.Parse<StopBits>(_config["ModbusRtu:StopBits"] ?? "One");
        private byte SlaveId => byte.Parse(_config["ModbusRtu:SlaveId"] ?? "1");




        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            _logger.LogInformation("MODBUS RTU后台服务正在启动...");

            while (!stoppingToken.IsCancellationRequested)
            {
                try
                {
                    // 串口断开则重新打开连接
                    if (_serialPort == null || !_serialPort.IsOpen || _modbusMaster == null)
                    {                        
                        await ConnectModbusRtuAsync(stoppingToken);
                    }

                    // Modbus读写业务
                    await ModbusReadWriteTask(stoppingToken);

                    await Task.Delay(5000, stoppingToken);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "串口报错..");
                    await Task.Delay(5000, stoppingToken);
                }
                await Task.Delay(1000, stoppingToken);
            }
        }

        /// <summary>
        /// 打开串口并创建Modbus RTU主站
        /// </summary>
        private async Task ConnectModbusRtuAsync(CancellationToken token)
        {
            await Task.Run(() =>
            {
                _logger.LogInformation($"正在打开串口 {ComPort} 波特率:{BaudRate} 从站ID:{SlaveId}");
                // 初始化串口参数
                _serialPort = new SerialPort(ComPort, BaudRate, Parity, DataBits, StopBits);
                _serialPort.ReadTimeout = 3000;
                _serialPort.WriteTimeout = 3000;
                _serialPort.Open();
                // 创建RTU主站
                _modbusMaster = ModbusSerialMaster.CreateRtu(_serialPort);
            }, token);

            _logger.LogInformation("Modbus RTU 串口连接成功！");
        }

        private async Task ModbusReadWriteTask(CancellationToken token)
        {
            ushort[] holdingRegs = null;
            try
            {
                // 1. 同步读取寄存器（Task.Run只包裹同步modbus读取）
                holdingRegs = await Task.Run(() =>
                {
                    // 读取100~132共33个保持寄存器
                    return _modbusMaster.ReadHoldingRegisters(SlaveId, startAddress: 100, numberOfPoints: 33);
                }, token);
                _logger.LogDebug("Modbus寄存器读取成功");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Modbus读取寄存器失败");
                return; // 读取失败直接退出本次循环，不执行入库
            }

            // ========== 直接取原始寄存器整数值存入数据库（不用÷10，数据库存放大后的整数） ==========
            // A相
            int va = holdingRegs[0];
            int ia = holdingRegs[1];
            int p_a = holdingRegs[2];
            int q_a = holdingRegs[3];
            int s_a = holdingRegs[4];
            int pf_a = holdingRegs[5];
            int thdv_a = holdingRegs[6];
            int thidi_a = holdingRegs[7];

            // B相
            int vb = holdingRegs[8];
            int ib = holdingRegs[9];
            int p_b = holdingRegs[10];
            int q_b = holdingRegs[11];
            int s_b = holdingRegs[12];
            int pf_b = holdingRegs[13];
            int thdv_b = holdingRegs[14];
            int thidi_b = holdingRegs[15];

            // C相
            int vc = holdingRegs[16];
            int ic = holdingRegs[17];
            int p_c = holdingRegs[18];
            int q_c = holdingRegs[19];
            int s_c = holdingRegs[20];
            int pf_c = holdingRegs[21];
            int thdv_c = holdingRegs[22];
            int thidi_c = holdingRegs[23];

            // 三相总参数
            int p_total = holdingRegs[24];
            int q_total = holdingRegs[25];
            // s_total 模型无字段，舍弃
            int pf_total = holdingRegs[27];
            int thdv_total = holdingRegs[28];
            int thdi_total = holdingRegs[29];

            // 2. 创建数据库作用域，插入数据（单独try捕获数据库异常）            
            try
            {                
                using (var scope = _scopeFactory.CreateScope())
                {
                    var dbContext = scope.ServiceProvider.GetRequiredService<AppDbContext>();

                    var dataModel = new tw_kzq
                    {
                        // id 自增，不赋值
                        va = va,
                        vb = vb,
                        vc = vc,
                        ia = ia,
                        ib = ib,
                        ic = ic,

                        p_a = p_a,
                        p_b = p_b, // 修复：原来写成p_c，现在修正
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

                    dbContext.twj_kzqs.Add(dataModel); // 修复：twj_kzqs → tw_kzqs
                    await dbContext.SaveChangesAsync(token);
                    //_logger.LogInformation("电表采集数据已成功写入数据库tw_kzq表");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "电表数据写入数据库失败");
            }            

            // ========== 换算浮点，打印日志展示真实物理值 ==========
            double aVol = va / 10.0;
            double aCur = ia / 10.0;
            double aP = p_a / 10.0;
            double aQ = q_a / 10.0;
            double aS = s_a / 10.0;
            double aPf = pf_a / 100.0;
            double aThdU = thdv_a / 10.0;
            double aThdI = thidi_a / 10.0;

            double bVol = vb / 10.0;
            double bCur = ib / 10.0;
            double bP = p_b / 10.0;
            double bQ = q_b / 10.0;
            double bS = s_b / 10.0;
            double bPf = pf_b / 100.0;
            double bThdU = thdv_b / 10.0;
            double bThdI = thidi_b / 10.0;

            double cVol = vc / 10.0;
            double cCur = ic / 10.0;
            double cP = p_c / 10.0;
            double cQ = q_c / 10.0;
            double cS = s_c / 10.0;
            double cPf = pf_c / 100.0;
            double cThdU = thdv_c / 10.0;
            double cThdI = thidi_c / 10.0;

            double totalP = p_total / 10.0;
            double totalQ = q_total / 10.0;
            double totalPf = pf_total / 100.0;
            double totalThdU = thdv_total / 10.0;
            double totalThdI = thdi_total / 10.0;

            //_logger.LogInformation("===== 三相电表实时数据 =====");
            //_logger.LogInformation($"A相：电压{aVol}V 电流{aCur}A 有功{aP}kW 无功{aQ}kVar 视在{aS}kVA 功率因数{aPf} 电压畸变{aThdU}% 电流畸变{aThdI}%");
            //_logger.LogInformation($"B相：电压{bVol}V 电流{bCur}A 有功{bP}kW 无功{bQ}kVar 视在{bS}kVA 功率因数{bPf} 电压畸变{bThdU}% 电流畸变{bThdI}%");
            //_logger.LogInformation($"C相：电压{cVol}V 电流{cCur}A 有功{cP}kW 无功{cQ}kVar 视在{cS}kVA 功率因数{cPf} 电压畸变{cThdU}% 电流畸变{cThdI}%");
            //_logger.LogInformation($"三相总和：有功{totalP}kW 无功{totalQ}kVar 总功率因数{totalPf} 总电压畸变{totalThdU}% 总电流畸变{totalThdI}%");
        }

        public ModbusService(ILogger<ModbusService> logger,
                                 IServiceScopeFactory scopeFactory,
                                 IConfiguration config)
        {
            //程序运行时只打印到控制台黑窗口，不会自动写入本地文件
            _logger = logger;
            _scopeFactory = scopeFactory; // 保存作用域工厂
            _config = config;
        }
    }
}
