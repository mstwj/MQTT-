using Newtonsoft.Json;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace 我在学习一下.Models
{
    public class DeviceParameter
    {
        [Key]
        public int Id { get; set; }  // 编号，自增

        // 外键：关联Device的DeviceCode（字符串类型）
        //[Required]
        [MaxLength(50)] // 与Device.DeviceCode长度保持一致
        [Display(Name = "设备编码")]
        [Required(ErrorMessage = "请选择设备")]
        public string? DeviceCode { get; set; }

        [ForeignKey("DeviceCode")]
        [JsonIgnore]
        public Device? Device { get; set; }

        [Display(Name = "参数名称")]
        [Required(ErrorMessage = "请输入参数名称")]
        public string? ParameterName { get; set; }

        [Display(Name = "访问地址")]
        [Required(ErrorMessage = "请输入访问地址")]
        public string? AccessAddress { get; set; }

        [Display(Name = "是否设备组属性")]
        public bool IsGroupProperty { get; set; }

        [Display(Name = "是否为累加参数")]
        public bool IsAccumulatedParameter { get; set; }

        [Display(Name = "单位")]
        public string? Unit { get; set; }

        [Display(Name = "创建时间")]
        [DataType(DataType.Date)]
        public DateTime? CreateTime { get; set; }

        [Display(Name = "更新时间")]
        [DataType(DataType.Date)]
        public DateTime? UpdateTime { get; set; }
    }
}
