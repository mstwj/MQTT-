using MQTTnet;
using MQTTnet.Client;
using System.Text;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

namespace MQTT客户端
{

    // 单条采集数据子对象
    public class MeterItem
    {
        public int scale { get; set; }
        public int raw { get; set; }
        public int addr { get; set; }
        public double real { get; set; }
    }

    // 根JSON对象
    public class MeterDataRoot
    {
        public MeterItem Ua { get; set; }
        public MeterItem Cabinet_Current_A { get; set; }
        public MeterItem Phase_A_Active_Power { get; set; }
        public MeterItem Sys_Freq_Ua { get; set; }
    }

    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        //hunbu/telemetry
        private IMqttClient _mqttClient;

        public MainWindow()
        {
            InitializeComponent();
        }

        private void Log(string msg)
        {
            Dispatcher.Invoke(() =>
            {
                lstLog.Items.Add($"[{DateTime.Now:HH:mm:ss}] {msg}");
                lstLog.ScrollIntoView(lstLog.Items[lstLog.Items.Count - 1]);
            });
        }

        private async void btnSubscribe_Click(object sender, RoutedEventArgs e)
        {
            if (_mqttClient == null || !_mqttClient.IsConnected)
            {
                Log("⚠️ 请先连接服务器");
                return;
            }

            var topic = txtSubscribeTopic.Text;
            await _mqttClient.SubscribeAsync(topic);
            Log($"📥 已订阅主题：{topic}");
        }

        private async void btnDisconnect_Click(object sender, RoutedEventArgs e)
        {
            if (_mqttClient != null && _mqttClient.IsConnected)
            {
                await _mqttClient.DisconnectAsync();
                Log("已断开连接");
            }
            btnConnect.IsEnabled = true;
            btnDisconnect.IsEnabled = false;
        }


        private async void btnPublish_Click(object sender, RoutedEventArgs e)
        {
            if (_mqttClient == null || !_mqttClient.IsConnected)
            {
                Log("⚠️ 请先连接服务器");
                return;
            }

            var message = new MqttApplicationMessageBuilder()
                .WithTopic(txtPublishTopic.Text)
                .WithPayload(Encoding.UTF8.GetBytes(txtPublishPayload.Text))
                .Build();

            await _mqttClient.PublishAsync(message);
            Log($"📤 已发布消息到 {txtPublishTopic.Text}：{txtPublishPayload.Text}");
        }

        private async void btnConnect_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var factory = new MqttFactory();
                _mqttClient = factory.CreateMqttClient();

                var options = new MqttClientOptionsBuilder()
                    .WithTcpServer(txtBroker.Text, int.Parse(txtPort.Text))
                    .WithClientId(txtClientId.Text)
                    .WithCleanSession()
                    .Build();

                _mqttClient.ApplicationMessageReceivedAsync += OnMessageReceived;

                await _mqttClient.ConnectAsync(options);

                Log("✅ 已连接到 MQTT 服务器");
                btnConnect.IsEnabled = false;
                btnDisconnect.IsEnabled = true;
            }
            catch (Exception ex)
            {
                Log($"❌ 连接失败：{ex.Message}");
            }
        }

        private async  Task OnMessageReceived(MqttApplicationMessageReceivedEventArgs args)
        {
            var topic = args.ApplicationMessage.Topic;
            var payload = Encoding.UTF8.GetString(args.ApplicationMessage.Payload);
            Log($"📥 收到 [{topic}]：{payload}");


            try
            {
                // 1. 反序列化JSON
                var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                var meterData = JsonSerializer.Deserialize<MeterDataRoot>(payload, options);

                if (meterData == null)
                {
                    Log("❌ JSON解析为空，丢弃本条数据");
                    return ;
                }

                // 2. 异步写入数据库（不阻塞MQTT消息循环）
                await DbHelper.InsertMeterDataAsync(topic, meterData);
                Log("✅ 数据入库成功");

                //Log($"📥 收到 [{topic}]：{meterData}");

            }
            catch (JsonException jsonEx)
            {
                Log($"❌ JSON格式解析失败：{jsonEx.Message}");
            }
            catch (Exception dbEx)
            {
                Log($"❌ 数据库写入异常：{dbEx.Message}");
            }
            
        }

    }
}