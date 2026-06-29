namespace MeterApi.Models
{
    public class MeterRecord
    {
        public long id { get; set; }
        public string? topic { get; set; }
        public DateTime collect_time { get; set; }
        public double? ua_real { get; set; }
        public double? cabinet_current_a { get; set; }
        public double? phase_a_active_power { get; set; }
        public double? sys_freq_ua { get; set; }
        public DateTime create_time { get; set; }
    }
}
