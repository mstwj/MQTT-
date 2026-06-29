using MySqlConnector;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace MQTT客户端
{
    public static class DbHelper
    {
        // 数据库连接字符串，自行修改地址账号库名
        private const string ConnStr = "server=172.30.135.213;user=root_remote;password=123456;database=test_db;SslMode=None";

        /// <summary>
        /// 异步写入电表数据
        /// </summary>
        public static async Task InsertMeterDataAsync(string topic, MeterDataRoot data)
        {
            const string sql = @"
            INSERT INTO device_meter_data 
            (topic, collect_time, ua_real, cabinet_current_a, phase_a_active_power, sys_freq_ua)
            VALUES 
            (@Topic, @CollectTime, @Ua, @CabCurrent, @APower, @Freq)
        ";

            // 当前时间作为采集时间
            var collectTime = DateTime.Now;

            await using var conn = new MySqlConnection(ConnStr);
            await conn.OpenAsync();

            await using var cmd = new MySqlCommand(sql, conn);
            cmd.Parameters.AddWithValue("@Topic", topic);
            cmd.Parameters.AddWithValue("@CollectTime", collectTime);
            cmd.Parameters.AddWithValue("@Ua", data.Ua.real);
            cmd.Parameters.AddWithValue("@CabCurrent", data.Cabinet_Current_A.real);
            cmd.Parameters.AddWithValue("@APower", data.Phase_A_Active_Power.real);
            cmd.Parameters.AddWithValue("@Freq", data.Sys_Freq_Ua.real);

            await cmd.ExecuteNonQueryAsync();
        }

    }
}
