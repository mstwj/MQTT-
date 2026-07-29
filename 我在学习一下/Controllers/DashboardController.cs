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



        public async Task<IActionResult> MyTest2()
        {
            /*
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
            */
            return Json(new
            {
                code = 500,
                msg = "查询失败"
            });

        }

        public async Task<IActionResult> MyTest()
        {
            try
            {
                // 核心改动：OrderByDescending + Take(10)
                var result = await _context.twj_kzqs
                    .OrderByDescending(x => x.create_time) // 时间倒序，最新在前
                    .Take(10)  // 只拿10条
                    .ToListAsync();

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
