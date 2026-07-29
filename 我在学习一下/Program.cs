using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using 我在学习一下.Data;

namespace 我在学习一下
{
    public class Program
    {
        public static void Main(string[] args)
        {
            //launchSettings.json 不是发布后生效的配置！
            //它只在 Visual Studio 内部调试时使用，你双击发布后的 exe，这个文件直接被忽略，完全无效。


            //appsettings.json【基础主配置】✅
            //无论开发、正式发布双击 exe、服务器部署，永远加载。
            //存放通用配置：数据库连接、Kestrel 端口、跨域、日志通用配置。
            //发布后，修改这个文件就能生效！这就是你要用来配置端口的文件！
            //appsettings.Development.json【开发环境专用】
            //只有程序环境变量 ASPNETCORE_ENVIRONMENT = Development 时才会加载。
            //也就是仅在 Visual Studio 里面点调试运行才生效；
            //✖️ 你双击 exe 运行【生产环境】，这个文件直接被忽略，完全不读取！

            // =====================【新增等待回车代码】=====================
            Console.WriteLine("=============================================");
            Console.WriteLine("服务初始化完成！按下回车键启动Web服务...");
            Console.WriteLine("=============================================");
            Console.ReadLine(); // 阻塞，等待用户输入回车

            var builder = WebApplication.CreateBuilder(args);


            // 1. 日志配置（Linux 路径，解决崩溃问题）
            builder.Logging.ClearProviders();

            // 2. CORS 配置（唯一策略，解决跨域）
            builder.Services.AddCors(options =>
            {
                options.AddPolicy("AllowAllCors", policy =>
                {
                    policy.AllowAnyOrigin()
                          .AllowAnyMethod()
                          .AllowAnyHeader();
                });
            });


            // 3. Session 服务
            builder.Services.AddSession(options =>
            {
                options.IdleTimeout = TimeSpan.FromHours(1);
                options.Cookie.HttpOnly = true;
            });



            // 4. 数据库上下文（保留需要的，删除多余）
            builder.Services.AddDbContext<我在学习一下.Data.AppDbContext>(options =>
                options.UseSqlServer(
                    builder.Configuration.GetConnectionString("SqlConnection")
                ));


            // 6. JSON 序列化配置
            builder.Services.AddControllers()
                .AddJsonOptions(options =>
                {
                    options.JsonSerializerOptions.Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping;
                });


            // Add services to the container.
            builder.Services.AddControllersWithViews();

            var app = builder.Build();

            // Configure the HTTP request pipeline.
            if (!app.Environment.IsDevelopment())
            {
                app.UseExceptionHandler("/Home/Error");
                // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
                app.UseHsts();
            }

            app.UseHttpsRedirection();
            app.UseStaticFiles();

            app.UseRouting();

            // =====================【重点添加这一行！！】=====================
            app.UseCors("AllowAllCors");

            app.UseAuthorization();

            app.MapControllerRoute(
                name: "default",
                pattern: "{controller=Home}/{action=Index}/{id?}");



            // 9. 数据库初始化
            //CreateScope() 创建局部服务作用域
            using (var scope = app.Services.CreateScope())
            {
                //拿到当前作用域下的服务提供者，用来获取注册好的服务
                var services = scope.ServiceProvider;
                try
                {
                    var context = services.GetRequiredService<AppDbContext>();
                    //如果数据库已经存在：直接跳过，不做任何修改
                    //EnsureCreated：只建库建表，不执行迁移记录，适合小型 Demo、内存库
                    context.Database.EnsureCreated();
                }
                catch (Exception ex)
                {
                    var logger = services.GetRequiredService<ILogger<Program>>();
                    logger.LogError(ex, "An error occurred creating the DB.");
                }
            }


            app.Run();
        }
    }
}
