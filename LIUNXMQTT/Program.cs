using MQTTnet;
using MQTTnet.Client;
using System.Net.Sockets;
using System.Text;

namespace LIUNXMQTT
{
    internal class Program
    {

        //hunbu/telemetry
        private static IMqttClient _mqttClient;

        static async Task Main(string[] args)
        {

            await ConnectMqtt();
            // 连接成功才订阅
            if (_mqttClient != null && _mqttClient.IsConnected)
            {
                await SubscribeMqtt();
            }
            //await SubscribeMqtt();
            Console.WriteLine("Hello, World!");
            // 阻塞主线程，程序常驻，直到你按下回车才退出
            Console.ReadLine();
        }

        // 全局日志封装
        static void Log(string msg)
        {
            // 打印 年-月-日 时:分:秒 + 日志内容
            Console.WriteLine($"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {msg}");
        }

        private static async Task SubscribeMqtt()
        {
            if (_mqttClient == null || !_mqttClient.IsConnected)
            {
                Log("⚠️ 请先连接服务器");
                return;
            }

            var topic = "hunbu/telemetry";
            await _mqttClient.SubscribeAsync(topic);
            Log($"📥 已订阅主题：{topic}");
        }

        private static  Task OnMessageReceived(MqttApplicationMessageReceivedEventArgs args)
        {
            var topic = args.ApplicationMessage.Topic;
            var payload = Encoding.UTF8.GetString(args.ApplicationMessage.Payload);
            Log($"📥 收到 [{topic}]：{payload}");
            return Task.CompletedTask;
        }


        private static async Task ConnectMqtt()
        {
            try
            {
                var factory = new MqttFactory();
                _mqttClient = factory.CreateMqttClient();

                var options = new MqttClientOptionsBuilder()
                    .WithTcpServer("8.138.205.184", 1883)
                    .WithClientId("TWJClient2")
                    .WithCleanSession()
                    .Build();

                _mqttClient.ApplicationMessageReceivedAsync += OnMessageReceived;

                await _mqttClient.ConnectAsync(options);

                Log("✅ 已连接到 MQTT 服务器");
            }
            catch (Exception ex)
            {
                Log($"❌ 连接失败：{ex.Message}");
            }
        }

    }
}
