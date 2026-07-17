using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Memory;
using System;
using 我在学习一下.Data;
using 我在学习一下.Models;
using static 我在学习一下.Models.ElectricitySummary;

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

        public async Task<IActionResult> MyTest4()
        {
            try
            {
                // 查询所有人员，顺带加载每个人对应的全部成绩
                var result = await _context.TwjTestTables
                    // 关联一对多成绩表
                    .Include(p => p.Scores)
                    .ToListAsync();

                var html = @"
                    <!DOCTYPE html>
                    <html lang='zh-CN'>
                    <head></head>
                    <body>
                    <h2>北理电碳表 - 实时电气参数（全部字段）</h2>
                    <div style='overflow-x:auto;'>
                    <table>
                        <tr>
                            <th>ID</th>
                            <th>名称</th>
                            <th>性别</th>
                            <th>年纪</th>
                        </tr>";
                foreach (var item in result)
                {
                    html += $@"
                    <tr>
                        <td>{item.Id}</td>
                        <td>{item.Name}</td>
                        <td>{item.Sex}</td>
                        <td>{item.Age}</td>
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

        public async Task<IActionResult> MyTest3()
        {
            try
            {
                // 查询所有人员，顺带加载每个人对应的全部成绩
                var personWithAllScore = await _context.TwjTestTables
                    // 关联一对多成绩表
                    .Include(p => p.Scores)
                    .ToListAsync();

                // 直接返回JSON，前端能看到每个人嵌套的成绩数组
                return Json(new
                {
                    code = 200,
                    msg = "查询成功",
                    data = personWithAllScore
                });
            }
            catch (Exception ex)
            {
                // 捕获异常返回错误信息
                Console.WriteLine($"查询人员成绩异常：{ex.Message}");
                return Json(new
                {
                    code = 500,
                    msg = "查询失败",
                    error = ex.Message
                });
            }
        }

        public async Task<IActionResult> MyTest2()
        {
            try
            {
                // 空值兜底：确保返回的列表不为null（无数据时返回空列表）
                var result = await _context.v_twj_test_table_sort_age.ToListAsync();

                // 返回JSON结果
                return Json(result);
            }
            catch (Exception ex)
            {
                // 异常日志记录（建议替换为日志框架，如Serilog/NLog）
                Console.WriteLine($"查询电表参数视图异常：{ex.Message}，堆栈：{ex.StackTrace}");

                // 兜底返回500错误，保证前端接收结构完整
                return StatusCode(500, new
                {
                    Error = "获取电表参数失败",
                    Detail = ex.Message,
                    Time = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff")
                });
            }

        }

        public async Task<IActionResult> MyTest()
        {
            //已经把全部数据读到内存了，直接用列表方法：
            var rawData = await _context.TwjTestTables
                .OrderByDescending(m => m.Name)
                .ToListAsync();

            // 获取列表最后一条，空列表返回null
            var lastItem = rawData.LastOrDefault();

            // 赋值结果
            var result = new
            {
                powerFactor = lastItem.Name,
                ambientTemperature = lastItem.Sex,                
            };

            Response.ContentType = "application/json; charset=utf-8";
            return Json(result);

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
    }
}
