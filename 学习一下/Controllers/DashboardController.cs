using Microsoft.AspNetCore.Mvc;

namespace 学习一下.Controllers
{
    public class DashboardController : Controller
    {
        public IActionResult Index()
        {
            return View();
        }
    }
}
