using System.ComponentModel.DataAnnotations;

namespace 我在学习一下.Models
{
    public class TwjTestTable
    {
        [Key]
        public long Id { get; set; }  // 编号，自增

        [Display(Name = "设备组名称")]
        [Required(ErrorMessage = "请输入设备组名称")]
        [MaxLength(64)]
        public string Name { get; set; }

        [Display(Name = "备注")]
        [MaxLength(5)]
        public string? Sex { get; set; }

        [Display(Name = "年龄")]
        public int? Age { get; set; }

        // 导航属性：一个人有多条成绩
        public List<TwjScore> Scores { get; set; } = new List<TwjScore>();

    }
}
