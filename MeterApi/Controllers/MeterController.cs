using MeterApi.Services;
using Microsoft.AspNetCore.Mvc;

namespace MeterApi.Controllers
{
    [ApiController]
    [Route("api/meter")]
    public class MeterController : ControllerBase
    {
        private readonly MeterDbService _dbService;
        public MeterController(MeterDbService dbService)
        {
            _dbService = dbService;
        }

        [HttpGet("test")]
        public IActionResult Test()
        {
            return Ok(new { code = 200, msg = "路由正常，服务能返回数据" });
        }

        [HttpGet("latest")]
        public async Task<IActionResult> GetLatest([FromQuery] int count = 100)
        {
            try
            {
                var data = await _dbService.GetLatestData(count);
                return Ok(new { code = 200, msg = "success", data });
            }
            catch (Exception ex)
            {
                // 出错直接返回错误信息
                return StatusCode(500, new { code = 500, msg = "查询异常", errorMsg = ex.Message });
            }
        }

        [HttpGet("range")]
        public async Task<IActionResult> GetRange([FromQuery] DateTime start, [FromQuery] DateTime end)
        {
            if (start >= end)
                return BadRequest(new { code = 400, msg = "起始时间不能大于结束时间" });
            var data = await _dbService.QueryByTime(start, end);
            return Ok(new { code = 200, msg = "success", data });
        }
    }
}
