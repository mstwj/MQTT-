using Microsoft.EntityFrameworkCore;
using System.Text.RegularExpressions;
using 我在学习一下.Models;
using static 我在学习一下.Models.ElectricitySummary;

namespace 我在学习一下.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options)
            : base(options)
        {
        }


        // 设备组表
        public DbSet<TwjTestTable> TwjTestTables { get; set; }

        public DbSet<TwjScore> TwjScores { get; set; }

        public DbSet<v_twj_test_table_sort_age> v_twj_test_table_sort_age { get; set; }

        

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {

            // 成绩表 关联 人员表
            modelBuilder.Entity<TwjScore>()
                .HasOne(s => s.Person)
                .WithMany(p => p.Scores)
                .HasForeignKey(s => s.PersonId)
                .HasPrincipalKey(p => p.Id);

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
