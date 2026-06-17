using LiveCharts;
using OfficeOpenXml;
using System.ComponentModel;
using System.Data;
using System.IO;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

namespace EXCEL表变图
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window, INotifyPropertyChanged
    {

        #region 图表绑定属性
        private string _chartTitle;
        public string ChartTitle
        {
            get => _chartTitle;
            set { _chartTitle = value; OnPropertyChanged(); }
        }

        private string _xAxisTitle;
        public string XAxisTitle
        {
            get => _xAxisTitle;
            set { _xAxisTitle = value; OnPropertyChanged(); }
        }

        private string _yAxisTitle;
        public string YAxisTitle
        {
            get => _yAxisTitle;
            set { _yAxisTitle = value; OnPropertyChanged(); }
        }

        public ChartValues<double> YAxisValues { get; set; }
        public List<string> XAxisLabels { get; set; }
        #endregion

        #region 私有变量
        private DataTable _currentExcelData;
        #endregion

        public MainWindow()
        {
            InitializeComponent();

            // 初始化绑定数据源
            YAxisValues = new ChartValues<double>();
            XAxisLabels = new List<string>();
            DataContext = this;


        }


        #region 选择Excel文件
        private void BtnSelectExcel_Click(object sender, RoutedEventArgs e)
        {
            // 打开文件选择对话框
            Microsoft.Win32.OpenFileDialog openFileDialog = new Microsoft.Win32.OpenFileDialog
            {
                Filter = "Excel文件 (*.xlsx)|*.xlsx",
                Title = "选择数据Excel文件",
                Multiselect = false
            };

            if (openFileDialog.ShowDialog() == true)
            {
                string filePath = openFileDialog.FileName;
                TxtFilePath.Text = filePath;

                try
                {
                    // 读取Excel所有Sheet名称
                    List<string> sheetNames = GetExcelSheetNames(filePath);

                    // 绑定Sheet下拉列表
                    CboSheetList.ItemsSource = sheetNames;
                    CboSheetList.SelectedIndex = 0;
                    CboSheetList.IsEnabled = true;

                    MessageBox.Show("Excel文件读取成功！请选择工作表和对应列", "成功", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"读取Excel文件失败：{ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                    ResetControls();
                }
            }
        }
        #endregion

        #region 工作表选择变化
        private void CboSheetList_SelectionChanged(object sender, System.Windows.Controls.SelectionChangedEventArgs e)
        {
            if (CboSheetList.SelectedItem == null) return;

            string selectedSheet = CboSheetList.SelectedItem.ToString();
            string filePath = TxtFilePath.Text;

            try
            {
                // 读取选中Sheet的全部数据
                _currentExcelData = ReadExcelSheetToDataTable(filePath, selectedSheet);

                // 绑定数据预览表格
                DgDataPreview.ItemsSource = _currentExcelData.DefaultView;

                // 提取所有列名，绑定X/Y轴下拉列表
                List<string> columnNames = _currentExcelData.Columns.Cast<DataColumn>().Select(c => c.ColumnName).ToList();
                CboXAxisColumn.ItemsSource = columnNames;
                CboYAxisColumn.ItemsSource = columnNames;
                CboXAxisColumn.SelectedIndex = 0;
                CboYAxisColumn.SelectedIndex = 1;
                CboXAxisColumn.IsEnabled = true;
                CboYAxisColumn.IsEnabled = true;
                BtnGenerateChart.IsEnabled = true;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"读取工作表数据失败：{ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                ResetControls();
            }
        }
        #endregion

        #region 生成图表
        private void BtnGenerateChart_Click(object sender, RoutedEventArgs e)
        {
            if (_currentExcelData == null || CboXAxisColumn.SelectedItem == null || CboYAxisColumn.SelectedItem == null)
            {
                MessageBox.Show("请先选择Excel文件、工作表和对应列", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            string xColumnName = CboXAxisColumn.SelectedItem.ToString();
            string yColumnName = CboYAxisColumn.SelectedItem.ToString();

            try
            {
                // 清空原有数据
                XAxisLabels.Clear();
                YAxisValues.Clear();

                // 遍历数据行，提取有效数据
                foreach (DataRow row in _currentExcelData.Rows)
                {
                    string xValue = row[xColumnName].ToString().Trim();
                    string yValue = row[yColumnName].ToString().Trim();

                    // 过滤空值
                    if (string.IsNullOrWhiteSpace(xValue) || string.IsNullOrWhiteSpace(yValue))
                        continue;

                    // 解析Y轴数值
                    if (double.TryParse(yValue, out double yNumericValue))
                    {
                        XAxisLabels.Add(xValue);
                        YAxisValues.Add(yNumericValue);
                    }
                }

                // 校验有效数据
                if (XAxisLabels.Count == 0)
                {
                    throw new Exception("未提取到有效数据！请检查选择的列是否包含正确的时间和数值");
                }

                // 设置图表标题和轴标题
                ChartTitle = $"{yColumnName} 随 {xColumnName} 变化趋势";
                XAxisTitle = xColumnName;
                YAxisTitle = yColumnName;

                // 刷新图表
                ChartMain.Update();

                MessageBox.Show($"图表生成成功！共加载 {XAxisLabels.Count} 条有效数据", "成功", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"生成图表失败：{ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
        #endregion

        #region 辅助方法
        // 获取Excel所有Sheet名称
        private List<string> GetExcelSheetNames(string filePath)
        {
            FileInfo fileInfo = new FileInfo(filePath);
            using (ExcelPackage package = new ExcelPackage(fileInfo))
            {
                return package.Workbook.Worksheets.Select(sheet => sheet.Name).ToList();
            }
        }

        // 读取指定Sheet到DataTable
        private DataTable ReadExcelSheetToDataTable(string filePath, string sheetName)
        {
            FileInfo fileInfo = new FileInfo(filePath);
            using (ExcelPackage package = new ExcelPackage(fileInfo))
            {
                ExcelWorksheet worksheet = package.Workbook.Worksheets[sheetName];
                DataTable dataTable = new DataTable(sheetName);

                // 读取表头（第一行）
                int colCount = worksheet.Dimension.End.Column;
                for (int col = 1; col <= colCount; col++)
                {
                    string header = worksheet.Cells[1, col].Text.Trim();
                    // 处理空列名
                    if (string.IsNullOrWhiteSpace(header))
                        header = $"列{col}";
                    dataTable.Columns.Add(header);
                }

                // 读取数据行
                int rowCount = worksheet.Dimension.End.Row;
                for (int row = 2; row <= rowCount; row++)
                {
                    DataRow dataRow = dataTable.NewRow();
                    for (int col = 1; col <= colCount; col++)
                    {
                        dataRow[col - 1] = worksheet.Cells[row, col].Text.Trim();
                    }
                    dataTable.Rows.Add(dataRow);
                }

                return dataTable;
            }
        }

        // 重置控件状态
        private void ResetControls()
        {
            CboSheetList.ItemsSource = null;
            CboSheetList.IsEnabled = false;
            CboXAxisColumn.ItemsSource = null;
            CboXAxisColumn.IsEnabled = false;
            CboYAxisColumn.ItemsSource = null;
            CboYAxisColumn.IsEnabled = false;
            BtnGenerateChart.IsEnabled = false;
            DgDataPreview.ItemsSource = null;
            _currentExcelData = null;
            XAxisLabels.Clear();
            YAxisValues.Clear();
            ChartMain.Update();
        }

        // 属性变更通知
        public event PropertyChangedEventHandler PropertyChanged;
        protected virtual void OnPropertyChanged(string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
        #endregion

    }
}