using Kzq_modbus;
using Kzq_modbus.Data;
using Microsoft.EntityFrameworkCore;
using System;

var host = Host.CreateDefaultBuilder(args)
    .ConfigureServices((hostContext, services) =>
    {
        // 注册DbContext（默认是Scoped生命周期，正确）
        var connectionString = hostContext.Configuration.GetConnectionString("SqlServerConnection");
        services.AddDbContext<AppDbContext>(options =>
            // 替换成SQL Server驱动，不需要版本参数
            options.UseSqlServer(connectionString));

        // 注册Worker服务（单例，正确）
        services.AddHostedService<ModbusService>();
    })
    .Build();

await host.RunAsync();