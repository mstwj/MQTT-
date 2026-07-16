using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Memory;
using System;
using 我在学习一下.Data;
using 我在学习一下.Models;

namespace 我在学习一下.Controllers
{
    public class DashboardController : Controller
    {

        private readonly AppDbContext _context;


        // ② 构造函数注入 IMemoryCache
        public DashboardController(AppDbContext context, IMemoryCache memoryCache)
        {
            _context = context;            
        }

        public IActionResult Index()
        {
            return View();
        }

        public async Task<IActionResult> deviceStatus()
        {
            try
            {
                // 假设在异步方法中（已添加 async 修饰符）
                // 1. 计算时间范围（最近24小时）
                DateTime now = DateTime.Now;
                // 计算起始整点：当前时间的前1小时（如18:30→17:00）
                DateTime currentHour = new DateTime(now.Year, now.Month, now.Day, now.Hour, 0, 0).AddHours(0);

                // 1. 生成24个整点时间（从currentHour往前推24小时）
                List<DateTime> hourlyTimes = new List<DateTime>();
                for (int i = 0; i < 24; i++)
                {
                    hourlyTimes.Add(currentHour.AddHours(-i)); // 17:00, 16:00, ..., 昨天18:00
                }
                hourlyTimes.Reverse(); // 反转后：从最早的时间（昨天18:00）到最近的时间（17:00

                // 生成本周日期标签（周一到周日）

                DateTime monday = now.AddDays(-(int)now.DayOfWeek + (int)DayOfWeek.Monday);
                // 计算本周日（周一往后推 6 天）
                DateTime sunday = monday.AddDays(6).AddHours(23).AddMinutes(59).AddSeconds(59);
                // 1. 计算时间范围（本月1号 至 当前日期+1天）
                Dictionary<int, string> weekdayMap = new Dictionary<int, string>()
                {
                    { 1, "周一" },
                    { 2, "周二" },
                    { 3, "周三" },
                    { 4, "周四" },
                    { 5, "周五" },
                    { 6, "周六" },
                    { 7, "周日" }
                };
                DateTime today = DateTime.Now;
                DateTime startOfMonth = new DateTime(today.Year, today.Month, 1); // 本月1号（包含）
                DateTime endOfToday = today.AddDays(0); // 当前日期+1天（不包含，即截止到今天23:59:59）





                var result = new
                {
                    deviceStatus = new
                    {

                        // 处理空数据（若表中无记录，设默认值 0）
                        running = 0,
                        stopped = 0,
                        fault = 0,
                        totalCarbonEmission = 0M,
                        cap1Temperature = 0M,
                        cap1Capacity = 0M,
                        cap1StatusA = 0M,
                        cap1StatusB = 0M,
                        cap1StatusC = 0M,
                        totalVoltageDistortion = 0M,
                        totalCurrentDistortion = 0M,
                        phaseAVoltageDistortion = 0M,
                        phaseBVoltageDistortion = 0M,
                        phaseCVoltageDistortion = 0M,
                        phaseACurrentDistortion = 0M,
                        phaseBCurrentDistortion = 0M,
                        phaseCCurrentDistortion = 0M
                    }
                };

                Response.ContentType = "application/json; charset=utf-8";
                return Json(result);
            }
            catch (Exception ex)
            {
                return Ok(new
                {
                    Error = ex.Message
                });
            }
        }


        public async Task<IActionResult> ChartData()
        {
            try
            {
                // ========== 1. 修正时间范围计算 ==========
                DateTime today = DateTime.Now;
                DateTime startOfMonth = new DateTime(today.Year, today.Month, 1); // 本月1号 00:00:00
                DateTime endOfToday = new DateTime(today.Year, today.Month, today.Day, 23, 59, 59); // 当天23:59:59


                // ========== 4. 构造和旧接口完全一致的返回结构 ==========
                var result = new
                {
                    ChartData = new
                    {

                    }
                };

                // ========== 5. 返回数据 ==========
                Response.ContentType = "application/json; charset=utf-8";
                return Json(result);
            }
            catch (Exception ex)
            {
                return Ok(new
                {
                    Error = ex.Message
                });
            }
        }

        public async Task<IActionResult> v_grid_power_data()
        {
            try
            {
                // 1. 定义默认值（统一为可空类型，匹配电网功率视图的所有字段）
                var defaultValue = new
                {
                    LatestCreateTime = (DateTime?)DateTime.MinValue,  // 最新记录时间（可空）
                                                                      // 视在功率（可空decimal，默认0）
                    AGridApparentPower = (decimal?)0m,
                    BGridApparentPower = (decimal?)0m,
                    CGridApparentPower = (decimal?)0m,
                    // 无功功率（可空decimal，默认0）
                    AGridReactivePower = (decimal?)0m,
                    BGridReactivePower = (decimal?)0m,
                    CGridReactivePower = (decimal?)0m,
                    // 有功功率（可空decimal，默认0）
                    AGridActivePower = (decimal?)0m,
                    BGridActivePower = (decimal?)0m,
                    CGridActivePower = (decimal?)0m,
                    // 功率因数（可空decimal，默认0）
                    AGridPowerFactor = (decimal?)0m,
                    BGridPowerFactor = (decimal?)0m,
                    CGridPowerFactor = (decimal?)0m
                };

                // 2. 查询v_grid_power_data视图（确保DbContext已注册该视图）
                //var gridData = await _context.v_grid_power_data
                    //.FirstOrDefaultAsync();

                // 3. 组装返回结果（可空类型完全对齐，无转换错误）
                var result = new
                {
                    /*
                    LatestCreateTime = gridData.latest_create_time,
                    // 视在功率
                    AGridApparentPower = gridData.a_grid_apparent_power.HasValue ? (decimal?)Convert.ToDecimal(gridData.a_grid_apparent_power.Value) : null,
                    BGridApparentPower = gridData.b_grid_apparent_power.HasValue ? (decimal?)Convert.ToDecimal(gridData.b_grid_apparent_power.Value) : null,
                    CGridApparentPower = gridData.c_grid_apparent_power.HasValue ? (decimal?)Convert.ToDecimal(gridData.c_grid_apparent_power.Value) : null,
                    // 无功功率
                    AGridReactivePower = gridData.a_grid_reactive_power.HasValue ? (decimal?)Convert.ToDecimal(gridData.a_grid_reactive_power.Value) : null,
                    BGridReactivePower = gridData.b_grid_reactive_power.HasValue ? (decimal?)Convert.ToDecimal(gridData.b_grid_reactive_power.Value) : null,
                    CGridReactivePower = gridData.c_grid_reactive_power.HasValue ? (decimal?)Convert.ToDecimal(gridData.c_grid_reactive_power.Value) : null,
                    // 有功功率
                    AGridActivePower = gridData.a_grid_active_power.HasValue ? (decimal?)Convert.ToDecimal(gridData.a_grid_active_power.Value) : null,
                    BGridActivePower = gridData.b_grid_active_power.HasValue ? (decimal?)Convert.ToDecimal(gridData.b_grid_active_power.Value) : null,
                    CGridActivePower = gridData.c_grid_active_power.HasValue ? (decimal?)Convert.ToDecimal(gridData.c_grid_active_power.Value) : null,
                    // 功率因数
                    AGridPowerFactor = gridData.a_grid_power_factor.HasValue ? (decimal?)Convert.ToDecimal(gridData.a_grid_power_factor.Value) : null,
                    BGridPowerFactor = gridData.b_grid_power_factor.HasValue ? (decimal?)Convert.ToDecimal(gridData.b_grid_power_factor.Value) : null,
                    CGridPowerFactor = gridData.c_grid_power_factor.HasValue ? (decimal?)Convert.ToDecimal(gridData.c_grid_power_factor.Value) : null
                    */
                };

                return Json(result);
            }
            catch (Exception ex)
            {
                // 日志记录
                Console.WriteLine($"查询电网功率数据异常：{ex.Message}\n堆栈：{ex.StackTrace}");
                // 异常返回（生产环境建议隐藏Detail）
                return StatusCode(500, new
                {
                    Error = "获取电网功率数据失败",
                    Detail = ex.Message,
                    Time = DateTime.Now
                });
            }
        }


        public async Task<IActionResult> v_electricity_beili()
        {
            try
            {
                // 直接查询视图
                var meterParams = await _context.Set<v_electricity_beili>()
                    .FromSqlRaw("SELECT * FROM v_electricity_beili ORDER BY `电表编号`")
                    .ToListAsync();

                var result = meterParams ?? new List<v_electricity_beili>();

                // 返回 HTML 网页（自动刷新2秒 + 显示全部字段版）
                var html = @"
<!DOCTYPE html>
<html lang='zh-CN'>
<head>
    <meta charset='UTF-8'>
    <!-- 每2秒自动刷新页面 -->
    <meta http-equiv='refresh' content='2'>
    <title>北理电碳表实时数据</title>
    <style>
        body { font-family: Microsoft YaHei; margin:20px; }
        table { width:100%; border-collapse:collapse; margin-top:10px; table-layout:fixed; }
        th,td { border:1px solid #ccc; padding:6px 8px; text-align:center; font-size:12px; }
        th { background:#0078d7; color:white; }
        tr:nth-child(even) { background:#f5f5f5; }
    </style>
</head>
<body>
    <h2>北理电碳表 - 实时电气参数（全部字段）</h2>
    <div style='overflow-x:auto;'>
    <table>
        <tr>
            <th>ID</th>
            <th>电表编号</th>
            <th>最新更新时间</th>
            <th>A相电压</th>
            <th>B相电压</th>
            <th>C相电压</th>
            <th>AB线电压</th>
            <th>BC线电压</th>
            <th>CA线电压</th>
            <th>A相电流</th>
            <th>B相电流</th>
            <th>C相电流</th>
            <th>零线电流</th>
            <th>A有功功率</th>
            <th>B有功功率</th>
            <th>C有功功率</th>
            <th>总有功功率</th>
            <th>A无功功率</th>
            <th>B无功功率</th>
            <th>C无功功率</th>
            <th>总无功功率</th>
            <th>A视在功率</th>
            <th>B视在功率</th>
            <th>C视在功率</th>
            <th>总视在功率</th>
            <th>A功率因数</th>
            <th>B功率因数</th>
            <th>C功率因数</th>
            <th>总功率因数</th>
            <th>功率方向</th>
        </tr>";

                foreach (var item in result)
                {
                    html += $@"
        <tr>
            <td>{item.ID}</td>
            <td>{item.电表编号}</td>
            <td>{item.最新更新时间?.ToString("yyyy-MM-dd HH:mm:ss") ?? "-"}</td>
            <td>{item.A相电压:#0.0000}</td>
            <td>{item.B相电压:#0.0000}</td>
            <td>{item.C相电压:#0.0000}</td>
            <td>{item.AB线电压:#0.0000}</td>
            <td>{item.BC线电压:#0.0000}</td>
            <td>{item.CA线电压:#0.0000}</td>
            <td>{item.A相电流:#0.0000}</td>
            <td>{item.B相电流:#0.0000}</td>
            <td>{item.C相电流:#0.0000}</td>
            <td>{item.零线电流:#0.0000}</td>
            <td>{item.A有功功率:#0.0000}</td>
            <td>{item.B有功功率:#0.0000}</td>
            <td>{item.C有功功率:#0.0000}</td>
            <td>{item.总有功功率:#0.0000}</td>
            <td>{item.A无功功率:#0.0000}</td>
            <td>{item.B无功功率:#0.0000}</td>
            <td>{item.C无功功率:#0.0000}</td>
            <td>{item.总无功功率:#0.0000}</td>
            <td>{item.A视在功率:#0.0000}</td>
            <td>{item.B视在功率:#0.0000}</td>
            <td>{item.C视在功率:#0.0000}</td>
            <td>{item.总视在功率:#0.0000}</td>
            <td>{item.A功率因数:#0.0000}</td>
            <td>{item.B功率因数:#0.0000}</td>
            <td>{item.C功率因数:#0.0000}</td>
            <td>{item.总功率因数:#0.0000}</td>
            <td>{item.功率方向:#0.0000}</td>
        </tr>";
                }

                html += @"
    </table>
    </div>
</body>
</html>";

                return Content(html, "text/html; charset=utf-8");
            }
            catch (Exception ex)
            {
                var errorHtml = $@"
<!DOCTYPE html>
<html>
<body style='color:red;font-size:16px;margin:20px;'>
    <h3>获取数据失败</h3>
    <p>错误：{ex.Message}</p>
    <p>时间：{DateTime.Now:yyyy-MM-dd HH:mm:ss}</p>
</body>
</html>";

                return Content(errorHtml, "text/html; charset=utf-8");
            }
        }

    }
}
