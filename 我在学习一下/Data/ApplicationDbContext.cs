using Microsoft.EntityFrameworkCore;
using 我在学习一下.Models;

namespace 我在学习一下.Data
{
    public class ApplicationDbContext : DbContext
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
            : base(options)
        {
        }

        // 设备组表
        public DbSet<DeviceGroup> DeviceGroups { get; set; }

        // 设备表
        public DbSet<Device> Devices { get; set; }

        // 设备参数表
        public DbSet<DeviceParameter> DeviceParameters { get; set; }

        // 设备参数数据表
        public DbSet<ParameterData> parameterdatas_copy5 { get; set; }

        // 设备报警数据表
        public DbSet<AlarmData> AlarmDatas { get; set; }



    }
}
