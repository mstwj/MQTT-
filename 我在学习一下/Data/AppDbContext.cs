using Microsoft.EntityFrameworkCore;
using System.Text.RegularExpressions;
using 我在学习一下.Models;
using static 我在学习一下.Models.ElectricitySummary;

namespace 我在学习一下.Data
{
    //以下很多代码无法使用,因为阿炳的PC机器,有人使用了.. 我现在使用的是 工程机发送..
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options)
            : base(options)
        {
        }



        public DbSet<tw_kzq> twj_kzqs { get; set; }
        

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {


            //EF Core 在第一次创建数据库模型（Model）时自动执行，只会运行一次。
            //配置实体关联：一对多、一对一、多对多（你现在用的就是一对多）
            // 设备与设备参数的关系：一对多

            // 关键配置：所有实体类对应的表名自动转为小写
            foreach (var entityType in modelBuilder.Model.GetEntityTypes())
            {
                // 将实体类名（如 DeviceGroups）转为小写（如 devicegroups）
                entityType.SetTableName(entityType.GetTableName().ToLower());

                // 可选：同时将列名也转为小写（避免字段名大小写问题）
                foreach (var property in entityType.GetProperties())
                {
                    string dbCol = Regex.Replace(property.Name, "(?<!^)([A-Z])", "_$1").ToLower();
                    property.SetColumnName(dbCol);
                }
            }

            // 保留你原本的其他配置（如种子数据、关系映射等）
            base.OnModelCreating(modelBuilder);

        }
    }
}
