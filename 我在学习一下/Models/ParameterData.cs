using System.ComponentModel.DataAnnotations;

namespace 我在学习一下.Models
{
    public class ParameterData
    {
        [Key]
        public int Id { get; set; }  // 编号，自增

        [Display(Name = "参数名称")]
        public string? ParameterName { get; set; }

        [Display(Name = "SN")]
        public string? SN { get; set; }  // 设备编码+“_”+访问地址

        [Display(Name = "ParameterId")]
        public int ParameterId { get; set; }  // 参数编号

        //public Device Device { get; set; }

        //保留外键（不影响数据库关联，仅不序列化导航属性）
        //public int DeviceId { get; set; }


        [Display(Name = "t")]
        public string? T { get; set; }

        [Display(Name = "单位")]
        public string? Unit { get; set; }

        [Display(Name = "数值")]
        public decimal Value { get; set; }

        [Display(Name = "时间")]
        public DateTime Time { get; set; }
    }
}
