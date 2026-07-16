using Microsoft.EntityFrameworkCore;
using 我在学习一下.Models;

namespace 我在学习一下.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options)
            : base(options)
        {
        }

        public IQueryable<ParameterData> GetParameterDataByTableName(string tableName)
        {
            // 利用 EF Core 的 FromSqlRaw 动态指定表名，返回 IQueryable
            return Set<ParameterData>().FromSqlRaw($"SELECT * FROM `{tableName}`");
        }

        // 设备组表
        public DbSet<DeviceGroup> DeviceGroups { get; set; }

        // 设备表
        public DbSet<Device> Devices { get; set; }

        // 设备参数表
        public DbSet<DeviceParameter> DeviceParameters { get; set; }

        // 设备参数数据表
        public DbSet<ParameterData> ParameterDatas { get; set; }

        // 设备报警数据表
        public DbSet<v_electricity_beili> v_electricity_beili { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {

            // 设备与设备参数的关系：一对多
            modelBuilder.Entity<DeviceParameter>()
                .HasOne(p => p.Device) // 每个参数属于一个设备
                .WithMany(d => d.Parameters) // 一个设备可以有多个参数（双向关联）
                .HasForeignKey(p => p.DeviceCode) // 外键是DeviceParameter.DeviceCode
                .HasPrincipalKey(d => d.DeviceCode);
        }
    }
}
