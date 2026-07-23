using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Kzq_modbus.Models
{
    public class tw_kzq
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int id { get; set; }
        public int va { get; set; }
        public int vb { get; set; }
        public int vc { get; set; }
        public int ia { get; set; }
        public int ib { get; set; }
        public int ic { get; set; }
        public int p_a { get; set; }
        public int p_b { get; set; }
        public int p_c { get; set; }
        public int q_a { get; set; }
        public int q_b { get; set; }
        public int q_c { get; set; }
        public int s_a { get; set; }
        public int s_b { get; set; }
        public int s_c { get; set; }

        public int pf_a { get; set; }
        public int pf_b { get; set; }
        public int pf_c { get; set; }

        public int thdv_a { get; set; }
        public int thdv_b { get; set; }
        public int thdv_c { get; set; }

        public int thidi_a { get; set; }
        public int thidi_b { get; set; }
        public int thidi_c { get; set; }

        public int p_total { get; set; }
        public int q_total { get; set; }
        public int pf_total { get; set; }
        public int thdv_total { get; set; }

        public int thdi_total { get; set; }

        public DateTime create_time { get; set; }
    }
}
