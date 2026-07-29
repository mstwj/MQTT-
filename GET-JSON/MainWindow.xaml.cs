using Modbus.Data;
using Modbus.Device;
using Modbus.Device;
using Newtonsoft.Json;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;


namespace GET_JSON
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        // HttpClient 建议全局只实例一次，不要每次请求new
        private static readonly HttpClient _httpClient = new HttpClient();

        private DataStore _dataStore;
        private ModbusTcpSlave _slaveServer;

        //寄存器监控
        private ushort[] _lastRegSnapshot = Array.Empty<ushort>();
        private CancellationTokenSource _registerMonitorCts;


        public MainWindow()
        {
            InitializeComponent();
        }

        private void BtnStart_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                //1. 创建寄存器仓库
                _dataStore = DataStoreFactory.CreateDefaultDataStore();

                //2. 【重点修复】手动创建TcpListener，代替直接填字符串IP
                IPAddress listenIp = IPAddress.Any; //等价0.0.0.0，监听所有网卡
                int port = 502;
                TcpListener listener = new TcpListener(listenIp, port);

                //3. 正确重载：CreateTcp(从站ID, TcpListener)
                _slaveServer = ModbusTcpSlave.CreateTcp(1, listener);
                _slaveServer.DataStore = _dataStore;
                _slaveServer.Listen();

                AddLog("Modbus从站启动成功！监听0.0.0.0:502");

                //启动寄存器数值监控
                _lastRegSnapshot = _dataStore.HoldingRegisters.ToArray();
                _registerMonitorCts = new CancellationTokenSource();
                _ = RegisterMonitorLoop(_registerMonitorCts.Token);
            }
            catch (Exception ex)
            {
                AddLog($"启动失败：{ex.Message}");
            }
        }

        private async Task RegisterMonitorLoop(CancellationToken token)
        {
            const int ScanIntervalMs = 100;
            while (!token.IsCancellationRequested)
            {
                try
                {
                    await Task.Delay(ScanIntervalMs, token);
                    // 读取当前寄存器快照
                    ushort[] currentRegs = _dataStore.HoldingRegisters.ToArray();

                    for (int addr = 0; addr < currentRegs.Length; addr++)
                    {
                        if (currentRegs[addr] != _lastRegSnapshot[addr])
                        {
                            Dispatcher.Invoke(() =>
                            {
                                AddLog($"【主机写入】保持寄存器 地址:{addr}，新值:{currentRegs[addr]}");
                            });
                            _lastRegSnapshot[addr] = currentRegs[addr];
                        }
                    }
                }
                catch (TaskCanceledException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    Dispatcher.Invoke(() =>
                    {
                        AddLog($"寄存器监控异常：{ex.Message}");
                    });
                }
            }
        }

        private void BtnStop_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                //停止监控
                _registerMonitorCts?.Cancel();
                _registerMonitorCts?.Dispose();
                _registerMonitorCts = null;

                //停止modbus
                _slaveServer?.Dispose();
                _slaveServer = null;
                _dataStore = null;
                AddLog("Modbus从站已停止");
            }
            catch (Exception ex)
            {
                AddLog($"停止失败：{ex.Message}");
            }
        }

        protected override void OnClosed(EventArgs e)
        {
            _registerMonitorCts?.Cancel();
            _registerMonitorCts?.Dispose();
            base.OnClosed(e);
        }
        // 本地手动写入保持寄存器
        

        private void AddLog(string msg)
        {
            string logLine = $"{DateTime.Now:HH:mm:ss} | {msg}";
            lstLog.Items.Add(logLine);
            lstLog.ScrollIntoView(lstLog.Items[lstLog.Items.Count - 1]);
        }

        //
        //[{
        //https://192.168.0.101/api/devcel2/getall
        //}
        //

        private async void BtnGet_Click(object sender, RoutedEventArgs e)
        {
            try
            {
            //string url = "https://192.168.0.101/api/devcel2/getall"; //替换成你的服务器地址
            string url = "http://192.168.0.101:8082/api/meter01/getAll"; //替换成你的服务器地址
            

                // 发送GET请求
                HttpResponseMessage response = await _httpClient.GetAsync(url);

                // 判断HTTP状态码是否成功（200~299）
                response.EnsureSuccessStatusCode();

                // 读取返回字符串
                string jsonText = await response.Content.ReadAsStringAsync();

                // 显示原始JSON
                ((TextBox)this.FindName("TextBox1")).Text = jsonText;

                // ========== 解析JSON为实体对象 ==========
                TodoModel data = JsonConvert.DeserializeObject<TodoModel>(jsonText);

                MessageBox.Show($"解析成功！userId={data.userId}, title={data.title}");
            }
            catch (Exception ex)
            {
                MessageBox.Show($"请求异常：{ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void BtnWriteLocalReg_Click(object sender, RoutedEventArgs e)
        {

        }
    }

    // 根据你接口返回的JSON结构创建实体类
    public class TodoModel
    {
        public int userId { get; set; }
        public int id { get; set; }
        public string title { get; set; }
        public bool completed { get; set; }
    }
}