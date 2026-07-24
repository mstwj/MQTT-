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

        // 注册共享数据实例（单例）
        services.AddSingleton(new SharedModbusData(33));

        // 注册Worker服务（单例，正确）
        services.AddHostedService<ModbusService>();

        // 新增 ModbusTCP从站后台服务
        services.AddHostedService<ModbusTcpSlaveService>();
    })
    .Build();

await host.RunAsync();