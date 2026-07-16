using Newtonsoft.Json;

namespace 我在学习一下.Models
{
    public class ChartData
    {
        [JsonProperty("dates")]
        public List<string> Dates { get; set; } = new List<string>();

        [JsonProperty("lastMonthValues")]
        public List<decimal> LastMonthValues { get; set; } = new List<decimal>();

        [JsonProperty("currentMonthValues")]
        public List<decimal> CurrentMonthValues { get; set; } = new List<decimal>();
    }

    public class v_electricity_beili
    {
        /// <summary>
        /// 自增ID
        /// </summary>
        public int ID { get; set; }

        /// <summary>
        /// 电表编号
        /// </summary>
        public string 电表编号 { get; set; }

        /// <summary>
        /// 最新更新时间
        /// </summary>
        public DateTime? 最新更新时间 { get; set; }

        // ================= 电压 =================
        /// <summary>
        /// A相电压
        /// </summary>
        public decimal? A相电压 { get; set; }

        /// <summary>
        /// B相电压
        /// </summary>
        public decimal? B相电压 { get; set; }

        /// <summary>
        /// C相电压
        /// </summary>
        public decimal? C相电压 { get; set; }

        /// <summary>
        /// AB线电压
        /// </summary>
        public decimal? AB线电压 { get; set; }

        /// <summary>
        /// BC线电压
        /// </summary>
        public decimal? BC线电压 { get; set; }

        /// <summary>
        /// CA线电压
        /// </summary>
        public decimal? CA线电压 { get; set; }

        // ================= 电流 =================
        /// <summary>
        /// A相电流
        /// </summary>
        public decimal? A相电流 { get; set; }

        /// <summary>
        /// B相电流
        /// </summary>
        public decimal? B相电流 { get; set; }

        /// <summary>
        /// C相电流
        /// </summary>
        public decimal? C相电流 { get; set; }

        /// <summary>
        /// 零线电流
        /// </summary>
        public decimal? 零线电流 { get; set; }

        // ================= 有功功率 =================
        /// <summary>
        /// A有功功率
        /// </summary>
        public decimal? A有功功率 { get; set; }

        /// <summary>
        /// B有功功率
        /// </summary>
        public decimal? B有功功率 { get; set; }

        /// <summary>
        /// C有功功率
        /// </summary>
        public decimal? C有功功率 { get; set; }

        /// <summary>
        /// 总有功功率
        /// </summary>
        public decimal? 总有功功率 { get; set; }

        // ================= 无功功率 =================
        /// <summary>
        /// A无功功率
        /// </summary>
        public decimal? A无功功率 { get; set; }

        /// <summary>
        /// B无功功率
        /// </summary>
        public decimal? B无功功率 { get; set; }

        /// <summary>
        /// C无功功率
        /// </summary>
        public decimal? C无功功率 { get; set; }

        /// <summary>
        /// 总无功功率
        /// </summary>
        public decimal? 总无功功率 { get; set; }

        // ================= 视在功率 =================
        /// <summary>
        /// A视在功率
        /// </summary>
        public decimal? A视在功率 { get; set; }

        /// <summary>
        /// B视在功率
        /// </summary>
        public decimal? B视在功率 { get; set; }

        /// <summary>
        /// C视在功率
        /// </summary>
        public decimal? C视在功率 { get; set; }

        /// <summary>
        /// 总视在功率
        /// </summary>
        public decimal? 总视在功率 { get; set; }

        // ================= 功率因数 =================
        /// <summary>
        /// A功率因数
        /// </summary>
        public decimal? A功率因数 { get; set; }

        /// <summary>
        /// B功率因数
        /// </summary>
        public decimal? B功率因数 { get; set; }

        /// <summary>
        /// C功率因数
        /// </summary>
        public decimal? C功率因数 { get; set; }

        /// <summary>
        /// 总功率因数
        /// </summary>
        public decimal? 总功率因数 { get; set; }

        // ================= 功率方向 =================
        /// <summary>
        /// 功率方向
        /// </summary>
        public decimal? 功率方向 { get; set; }
    }
}
