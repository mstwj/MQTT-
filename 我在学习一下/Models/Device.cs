using Newtonsoft.Json;
using System.ComponentModel.DataAnnotations;

namespace 我在学习一下.Models
{
    public class Device
    {
        [Key]
        public int Id { get; set; }  // 编号，自增


        public int GroupId { get; set; } // 关键：确保字段名是 GroupId

        [JsonIgnore]
        public DeviceGroup? DeviceGroup { get; set; }



        [Display(Name = "设备名称")]
        [Required(ErrorMessage = "请输入设备名称")]
        public string? DeviceName { get; set; }

        [Display(Name = "设备编码")]
        [Required(ErrorMessage = "请输入设备编码")]
        public string? DeviceCode { get; set; }

        [Display(Name = "设备类型")]
        [Required(ErrorMessage = "请选择设备类型")]
        public string? DeviceType { get; set; }  // 电表、自动补偿控制器

        [Display(Name = "设备品牌")]
        public string? Brand { get; set; }

        [Display(Name = "设备型号")]
        public string? Model { get; set; }

        [Display(Name = "出厂日期")]
        [DataType(DataType.Date)]
        public DateTime? ManufactureDate { get; set; }

        [Display(Name = "购买日期")]
        [DataType(DataType.Date)]
        public DateTime? PurchaseDate { get; set; }

        [Display(Name = "出厂编号")]
        public string? FactoryNumber { get; set; }

        [Display(Name = "安装机位")]
        public string? InstallationLocation { get; set; }

        [Display(Name = "备注")]
        public string? Remarks { get; set; }

        [Display(Name = "状态")]
        public bool IsOnline { get; set; }

        [Display(Name = "创建时间")]
        [DataType(DataType.Date)]
        public DateTime? CreateTime { get; set; }

        [Display(Name = "更新时间")]
        [DataType(DataType.Date)]
        public DateTime? UpdateTime { get; set; }

        // 添加参数集合导航属性（一个设备包含多个参数）
        public ICollection<DeviceParameter> Parameters { get; set; } = new List<DeviceParameter>();


        // 添加这个集合属性：一个设备可以有多个报警数据
        public ICollection<AlarmData> AlarmDatas { get; set; } = new List<AlarmData>();

    }
}
