using MeterApi.Models;
using Microsoft.Extensions.Configuration;
using MySqlConnector;
using System.Data;


namespace MeterApi.Services
{
    public class MeterDbService
    {
        private readonly string _connStr;
        public MeterDbService(IConfiguration config)
        {
            _connStr = config.GetConnectionString("MeterDb")!;
        }

        public async Task<List<MeterRecord>> GetLatestData(int count = 100)
        {
            var list = new List<MeterRecord>();
            string sql = $"SELECT * FROM device_meter_data ORDER BY collect_time DESC LIMIT {count}";
            await using var conn = new MySqlConnection(_connStr);
            await conn.OpenAsync();
            await using var cmd = new MySqlCommand(sql, conn);
            await using var reader = await cmd.ExecuteReaderAsync();
            while (await reader.ReadAsync())
            {
                list.Add(new MeterRecord
                {
                    id = reader.GetInt64("id"),
                    topic = reader.IsDBNull("topic") ? null : reader.GetString("topic"),
                    collect_time = reader.GetDateTime("collect_time"),
                    ua_real = reader.IsDBNull("ua_real") ? null : reader.GetDouble("ua_real"),
                    cabinet_current_a = reader.IsDBNull("cabinet_current_a") ? null : reader.GetDouble("cabinet_current_a"),
                    phase_a_active_power = reader.IsDBNull("phase_a_active_power") ? null : reader.GetDouble("phase_a_active_power"),
                    sys_freq_ua = reader.IsDBNull("sys_freq_ua") ? null : reader.GetDouble("sys_freq_ua"),
                    create_time = reader.GetDateTime("create_time")
                });
            }
            return list;
        }

        public async Task<List<MeterRecord>> QueryByTime(DateTime start, DateTime end)
        {
            var list = new List<MeterRecord>();
            string sql = "SELECT * FROM device_meter_data WHERE collect_time BETWEEN @start AND @end ORDER BY collect_time ASC";
            await using var conn = new MySqlConnection(_connStr);
            await conn.OpenAsync();
            await using var cmd = new MySqlCommand(sql, conn);
            cmd.Parameters.AddWithValue("@start", start);
            cmd.Parameters.AddWithValue("@end", end);
            await using var reader = await cmd.ExecuteReaderAsync();
            while (await reader.ReadAsync())
            {
                list.Add(new MeterRecord
                {
                    id = reader.GetInt64("id"),
                    topic = reader.IsDBNull("topic") ? null : reader.GetString("topic"),
                    collect_time = reader.GetDateTime("collect_time"),
                    ua_real = reader.IsDBNull("ua_real") ? null : reader.GetDouble("ua_real"),
                    cabinet_current_a = reader.IsDBNull("cabinet_current_a") ? null : reader.GetDouble("cabinet_current_a"),
                    phase_a_active_power = reader.IsDBNull("phase_a_active_power") ? null : reader.GetDouble("phase_a_active_power"),
                    sys_freq_ua = reader.IsDBNull("sys_freq_ua") ? null : reader.GetDouble("sys_freq_ua"),
                    create_time = reader.GetDateTime("create_time")
                });
            }
            return list;
        }
    }
}
