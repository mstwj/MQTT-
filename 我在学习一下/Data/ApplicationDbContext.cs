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

        public DbSet<TwjTestTable> TwjTestTables { get; set; }

    }
}
