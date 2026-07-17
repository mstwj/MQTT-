using System.ComponentModel.DataAnnotations;

namespace 我在学习一下.Models
{
    public class ElectricitySummary
    {
        public class v_twj_test_table_sort_age
        {
            public long Id { get; set; }  // 编号，自增
            public string Name { get; set; }
            public string? Sex { get; set; }
            public int? Age { get; set; }

        }
    }
}
