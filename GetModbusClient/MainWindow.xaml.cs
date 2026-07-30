using Newtonsoft.Json;
using Newtonsoft.Json.Serialization;
using NModbus;
using NModbus.Serial;
using System.IO;
using System.IO.Ports;
using System.Net.Http;
using System.Text;
using System.Windows;
using System.Windows.Controls;

namespace GetModbusClient
{
    /// <summary>
    /// 配置模型 config.json
    /// </summary>
    public class AppConfig
    {
        // 串口参数
        public string ComName { get; set; } = "";
        public int BaudRate { get; set; } = 9600;
        public Parity Parity { get; set; } = Parity.None;
        public int DataBits { get; set; } = 8;
        public StopBits StopBits { get; set; } = StopBits.One;

        // Modbus 参数
        public byte SlaveId { get; set; } = 1;
        public ushort StartAddr { get; set; } = 0;
        public ushort ReadLength { get; set; } = 10;
        public int PollIntervalMs { get; set; } = 1000;

        // 后端服务地址
        public string ServerIp { get; set; } = "127.0.0.1";
        public int ServerPort { get; set; } = 5000;
    }


    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        private SerialPort _serialPort = null!;
        private IModbusMaster _modbusMaster = null!;
        private CancellationTokenSource? _pollCts;
        private bool _isRunning = false;
        // 全局HttpClient 放在类最上方
        private readonly HttpClient _httpClient = new HttpClient();

        // 配置文件路径
        private readonly string _configPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "config.json");
        private AppConfig _config = new AppConfig();

        
        /// <summary>
        /// 读取配置文件，不存在则创建默认配置
        /// </summary>
        private void LoadConfig()
        {
            try
            {
                if (File.Exists(_configPath))
                {
                    string json = File.ReadAllText(_configPath, Encoding.UTF8);
                    _config = JsonConvert.DeserializeObject<AppConfig>(json) ?? new AppConfig();
                    AddLog("✅成功加载配置文件 config.json");
                }
                else
                {
                    // 文件不存在，生成默认配置并保存
                    SaveConfig();
                    AddLog("⚠️未找到配置文件，已生成默认config.json");
                }
            }
            catch (Exception ex)
            {
                AddLog($"❌加载配置失败，使用默认参数：{ex.Message}");
                _config = new AppConfig();
            }
        }

        /// <summary>
        /// 保存当前配置到文件
        /// </summary>
        private void SaveConfig()
        {
            try
            {
                // 先从界面读取最新参数写入_config对象
                ReadUiToConfig();

                var jsonSetting = new JsonSerializerSettings
                {
                    ContractResolver = new CamelCasePropertyNamesContractResolver(),
                    Formatting = Formatting.Indented
                };
                string json = JsonConvert.SerializeObject(_config, jsonSetting);
                File.WriteAllText(_configPath, json, Encoding.UTF8);
                AddLog("✅配置已保存至 config.json");
            }
            catch (Exception ex)
            {
                AddLog($"❌保存配置失败：{ex.Message}");
            }
        }

        /// <summary>
        /// 界面控件 → 配置对象
        /// </summary>
        private void ReadUiToConfig()
        {
            // COM名称
            if (cbbCom.SelectedItem != null)
                _config.ComName = cbbCom.SelectedItem.ToString()!;

            // 波特率
            if (int.TryParse(cbbBaud.SelectedItem?.ToString(), out int baud))
                _config.BaudRate = baud;

            // 校验位
            if (Enum.TryParse<Parity>(cbbParity.SelectedItem?.ToString(), out var parity))
                _config.Parity = parity;

            // 数据位
            if (int.TryParse(cbbDataBit.SelectedItem?.ToString(), out int databit))
                _config.DataBits = databit;

            // 停止位
            if (int.TryParse(cbbStopBit.SelectedItem?.ToString(), out int stopNum))
                _config.StopBits = (StopBits)stopNum;

            // Modbus参数
            if (byte.TryParse(txtSlaveId.Text, out var sid)) _config.SlaveId = sid;
            if (ushort.TryParse(txtStartAddr.Text, out var addr)) _config.StartAddr = addr;
            if (ushort.TryParse(txtReadLen.Text, out var len)) _config.ReadLength = len;
            if (int.TryParse(txtInterval.Text, out var interval)) _config.PollIntervalMs = interval;

            // 服务器
            _config.ServerIp = txtServerIp.Text.Trim();
            if (int.TryParse(txtServerPort.Text, out var port)) _config.ServerPort = port;
        }



        public MainWindow()
        {
            InitializeComponent();
            InitComList();

            // ========== 程序启动加载配置 ==========
            LoadConfig();

            // 将配置数据填充到界面控件
            BindConfigToUi();

            cbbBaud.SelectedIndex = 0;
            cbbParity.SelectedIndex = 0;
            cbbDataBit.SelectedIndex = 0;
            cbbStopBit.SelectedIndex = 0;

            // HTTP超时
            _httpClient.Timeout = TimeSpan.FromSeconds(3);
        }

        //【建议你在界面新增按钮：保存配置，绑定这个事件】
        private void BtnSaveConfig_Click(object sender, RoutedEventArgs e)
        {
            SaveConfig();
        }

        /// <summary>
        /// 配置数据 → 界面控件
        /// </summary>
        private void BindConfigToUi()
        {
            // COM口（存在才选中）
            if (!string.IsNullOrEmpty(_config.ComName) && cbbCom.Items.Contains(_config.ComName))
            {
                cbbCom.SelectedItem = _config.ComName;
            }

            // 波特率
            SelectComboBoxItemByContent(cbbBaud, _config.BaudRate.ToString());
            // 校验位
            SelectComboBoxItemByContent(cbbParity, _config.Parity.ToString());
            // 数据位
            SelectComboBoxItemByContent(cbbDataBit, _config.DataBits.ToString());
            // 停止位
            SelectComboBoxItemByContent(cbbStopBit, ((int)_config.StopBits).ToString());

            // Modbus文本框
            txtSlaveId.Text = _config.SlaveId.ToString();
            txtStartAddr.Text = _config.StartAddr.ToString();
            txtReadLen.Text = _config.ReadLength.ToString();
            txtInterval.Text = _config.PollIntervalMs.ToString();

            // 服务端
            txtServerIp.Text = _config.ServerIp;
            txtServerPort.Text = _config.ServerPort.ToString();
        }

        /// <summary>
        /// 辅助方法：根据内容选中ComboBox项
        /// </summary>
        private void SelectComboBoxItemByContent(ComboBox cbb, string content)
        {
            foreach (var item in cbb.Items)
            {
                if (item.ToString() == content)
                {
                    cbb.SelectedItem = item;
                    break;
                }
            }
        }


        /// <summary>
        /// 扫描本地COM口
        /// </summary>
        private void InitComList()
        {
            cbbCom.Items.Clear();
            var ports = SerialPort.GetPortNames();
            foreach (var p in ports)
                cbbCom.Items.Add(p);
            if (ports.Length > 0)
                cbbCom.SelectedIndex = 0;
        }

        private void AddLog(string msg)
        {
            Dispatcher.Invoke(() =>
            {
                txtLog.AppendText($"[{DateTime.Now:HH:mm:ss}] {msg}\r\n");
                txtLog.ScrollToEnd();
            });
        }

        private void BtnClearLog_Click(object sender, RoutedEventArgs e)
        {
            txtLog.Clear();
        }

        private async void BtnStart_Click(object sender, RoutedEventArgs e)
        {
            if (_isRunning) return;
            try
            {
                // COM口
                string comName = cbbCom.SelectedItem?.ToString();
                if (string.IsNullOrWhiteSpace(comName))
                {
                    AddLog("请选择COM端口");
                    return;
                }
                

                // 波特率
                var baudItem = cbbBaud.SelectedItem as ComboBoxItem;
                if (baudItem == null || !int.TryParse(baudItem.Content.ToString(), out int baud))
                {
                    AddLog("波特率选择错误");
                    return;
                }

                // 校验位
                var parityItem = cbbParity.SelectedItem as ComboBoxItem;
                if (parityItem == null || !Enum.TryParse<Parity>(parityItem.Content.ToString(), out Parity parity))
                {
                    AddLog("校验位选择错误");
                    return;
                }

                // 数据位
                var dataBitItem = cbbDataBit.SelectedItem as ComboBoxItem;
                if (dataBitItem == null || !int.TryParse(dataBitItem.Content.ToString(), out int databit))
                {
                    AddLog("数据位选择错误");
                    return;
                }

                // 停止位
                var stopBitItem = cbbStopBit.SelectedItem as ComboBoxItem;
                if (stopBitItem == null || !int.TryParse(stopBitItem.Content.ToString(), out int stopBitNum))
                {
                    AddLog("停止位选择错误");
                    return;
                }
                StopBits stopbit = (StopBits)stopBitNum;

                // Modbus文本框参数
                if (!byte.TryParse(txtSlaveId.Text, out byte slaveId))
                {
                    AddLog("从站ID格式错误");
                    return;
                }
                if (!ushort.TryParse(txtStartAddr.Text, out ushort startAddr))
                {
                    AddLog("起始地址格式错误");
                    return;
                }
                if (!ushort.TryParse(txtReadLen.Text, out ushort readLength))
                {
                    AddLog("读取数量格式错误");
                    return;
                }
                if (!int.TryParse(txtInterval.Text, out int interval) || interval <= 0)
                {
                    AddLog("轮询间隔必须大于0");
                    return;
                }
                

                // 初始化串口 + Modbus RTU主机
                _serialPort = new SerialPort(comName, baud, parity, databit, stopbit);
                _serialPort.Open();

                IModbusFactory factory = new ModbusFactory();
                var adapter = new SerialPortAdapter(_serialPort);
                _modbusMaster = factory.CreateRtuMaster(adapter);
                _modbusMaster.Transport.ReadTimeout = 800;
                _modbusMaster.Transport.WriteTimeout = 800;

                _isRunning = true;
                btnStart.IsEnabled = false;
                btnStop.IsEnabled = true;
                _pollCts = new CancellationTokenSource();
                AddLog($"串口打开成功：{comName}，开始轮询");

                await PollLoop(slaveId, startAddr, readLength, interval, _pollCts.Token);
            }
            catch (Exception ex)
            {
                AddLog($"启动失败：{ex.Message}");
                CloseResource();
            }
        }

        /// <summary>
        /// 轮询循环：读取寄存器 → 生成JSON → 发送服务端
        /// </summary>
        private async Task PollLoop(byte slaveId, ushort startAddr, ushort readLen, int delayMs, CancellationToken token)
        {
            // JSON序列化配置：小驼峰（后端主流规范）
            var jsonSetting = new JsonSerializerSettings
            {
                ContractResolver = new CamelCasePropertyNamesContractResolver(),
                Formatting = Formatting.Indented
            };

            while (!token.IsCancellationRequested)
            {
                try
                {
                    // 03功能码 读取保持寄存器
                    ushort[] regs = _modbusMaster.ReadHoldingRegisters(slaveId, startAddr, readLen);

                    // ====== 组装JSON模型 ======
                    var dataModel = new
                    {
                        SlaveId = slaveId,
                        StartAddress = startAddr,
                        ReadCount = readLen,
                        Time = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                        Registers = regs
                    };
                    string json = JsonConvert.SerializeObject(dataModel, jsonSetting);
                    AddLog("采集成功\r\n" + json);

                    // 后台异步上传，不阻塞采集周期
                    _ = SendDataToServer(json);
                }
                catch (Exception ex)
                {
                    AddLog($"读取异常：{ex.Message}");
                }

                await Task.Delay(delayMs, token);
            }
        }

        private async Task SendDataToServer(string json)
        {
            try
            {
                string ip = txtServerIp.Text.Trim();
                string portStr = txtServerPort.Text.Trim();

                if (string.IsNullOrWhiteSpace(ip) || !int.TryParse(portStr, out int port))
                {
                    AddLog("服务器IP/端口配置错误");
                    return;
                }
                string url = $"http://{ip}:{port}/api/upload";
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                var resp = await _httpClient.PostAsync(url, content);

                if (resp.IsSuccessStatusCode)
                {
                    AddLog($"✅上传成功 {DateTime.Now:HH:mm:ss}");
                }
                else
                {
                    string resText = await resp.Content.ReadAsStringAsync();
                    AddLog($"❌上传失败 状态码:{(int)resp.StatusCode} 返回：{resText}");
                }
            }
            catch (Exception ex)
            {
                AddLog($"❌上传异常：{ex.Message}");
            }
        }

        private void BtnStop_Click(object sender, RoutedEventArgs e)
        {
            _pollCts?.Cancel();
            CloseResource();
            AddLog("采集已停止");
        }

        private void CloseResource()
        {
            _isRunning = false;
            btnStart.IsEnabled = true;
            btnStop.IsEnabled = false;

            if (_modbusMaster != null)
                _modbusMaster.Dispose();

            if (_serialPort != null && _serialPort.IsOpen)
                _serialPort.Close();

            _pollCts?.Dispose();
        }

        protected override void OnClosed(EventArgs e)
        {
            CloseResource();
            _httpClient.Dispose();
            base.OnClosed(e);
        }
    }
}
