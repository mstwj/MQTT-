using System.Text.Json.Serialization;
using System.ComponentModel.DataAnnotations.Schema;

namespace 我在学习一下.Models
{
    public class TwjScore
    {
        public long Id { get; set; }
        // 外键，对应人员表Id
        public long PersonId { get; set; }
        public string Subject { get; set; }
        public int Score { get; set; }

        //[Column("create_time")]
        public DateTime CreateTime { get; set; }

        // 导航属性：这条成绩属于哪一个人
        [JsonIgnore]
        public TwjTestTable Person { get; set; }
    }
}
