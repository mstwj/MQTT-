using System.ComponentModel.DataAnnotations;

namespace 我在学习一下.Models
{
    public class DeviceGroup
    {
        [Key]
        public int Id { get; set; }  // 编号，自增

        [Display(Name = "设备组名称")]
        [Required(ErrorMessage = "请输入设备组名称")]
        public string? GroupName { get; set; }

        [Display(Name = "备注")]
        public string? Description { get; set; }

        [Display(Name = "经度")]
        public decimal? Longitude { get; set; }

        [Display(Name = "纬度")]
        public decimal? Latitude { get; set; }

        [Display(Name = "公司名称")]
        public string? CompanyName { get; set; }

        [Display(Name = "创建时间")]
        public DateTime CreateTime { get; set; }

        [Display(Name = "更新时间")]
        public DateTime UpdateTime { get; set; }

        // 添加设备集合（一个设备组包含多个设备）
        public ICollection<Device> Devices { get; set; } = new List<Device>();

    }
}
