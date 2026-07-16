using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace 我在学习一下.Models
{
    public class AlarmData
    {
        [Key]
        public int Id { get; set; }  // 编号，自增



        [Display(Name = "设备名称")]
        public string? DeviceName { get; set; }

        // 外键：关联Device.Code（string类型）
        [Required]
        [MaxLength(50)] // 与Device.Code长度一致
        [Display(Name = "设备编码")]
        public string? DeviceCode { get; set; }


        [ForeignKey("DeviceCode")]
        public Device? Device { get; set; }

        [Display(Name = "报警类型")]
        public string? AlarmType { get; set; }

        [Display(Name = "值")]
        public decimal Value { get; set; }

        [Display(Name = "报警时间")]
        public DateTime AlarmTime { get; set; }

        [Display(Name = "报警信息")]
        public string? AlarmInfo { get; set; }

    }
}
