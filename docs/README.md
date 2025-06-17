# 📈 股票分析系统

一个基于 Python 的专业股票分析工具，提供技术指标计算、图表生成和网页界面。支持 A 股市场数据获取和分析。

## 🌟 功能特性

- **📊 技术指标分析**：MACD、RSI、布林带等专业技术指标
- **📈 交互式图表**：基于 Plotly 的专业 K 线图和技术指标图表
- **🌐 网页界面**：现代化的响应式网页界面，支持手机和电脑访问
- **⏰ 时间区间选择**：灵活的自定义分析时间范围
- **🔄 实时数据**：基于 akshare 获取最新的 A 股市场数据
- **📱 移动端适配**：完美支持移动设备访问

## 🏗️ 项目结构

```
my_cursor/
├── app.py                      # Flask 网页应用主文件
├── stock_analyzer.py           # 股票分析核心模块
├── demo.py                     # 命令行演示脚本
├── templates/
│   └── index.html             # 网页界面模板
├── __pycache__/               # Python 缓存文件
├── *.html                     # 生成的图表文件
└── README.md                  # 项目说明文档
```

## 📋 系统要求

- **Python**: 3.8+
- **操作系统**: Windows/Linux/macOS
- **内存**: 建议 4GB+
- **网络**: 需要互联网连接获取股票数据

## 🚀 快速开始

### 🐍 Anaconda 环境安装与配置

#### 1. 安装 Anaconda

如果您还没有安装 Anaconda，请按以下步骤操作：

**Windows:**
1. 访问 [Anaconda 官网](https://www.anaconda.com/products/distribution)
2. 下载 Python 3.10 版本的安装包
3. 运行安装程序，接受默认设置
4. 安装完成后，在开始菜单找到 "Anaconda Prompt"

**Linux/macOS:**
```bash
# 下载安装脚本
wget https://repo.anaconda.com/archive/Anaconda3-2023.09-Linux-x86_64.sh
# 或使用 curl
curl -O https://repo.anaconda.com/archive/Anaconda3-2023.09-Linux-x86_64.sh

# 运行安装脚本
bash Anaconda3-2023.09-Linux-x86_64.sh

# 重新加载 shell 配置
source ~/.bashrc
```

#### 2. 创建专用环境

```bash
# 创建新环境
conda create -n stock_analysis python=3.10 -y

# 激活环境
conda activate stock_analysis

# 验证环境
python --version  # 应显示 Python 3.10.x
```

#### 3. 安装依赖包

**方法一：使用 conda 安装（推荐）**
```bash
# 安装主要科学计算包
conda install pandas numpy matplotlib -c conda-forge -y

# 安装绘图和网页框架
conda install plotly flask -c conda-forge -y

# 使用 pip 安装特定包
pip install akshare talib-binary beautifulsoup4 lxml
```

**方法二：批量安装**
```bash
# 从 requirements.txt 安装
pip install -r config/requirements.txt
```

### 1. 环境准备

```bash
# 创建 conda 环境
conda create -n stock_analysis python=3.10 -y
conda activate stock_analysis

# 安装依赖包
pip install akshare pandas numpy plotly flask talib
```

### 2. 启动网页应用

```bash
# 启动 Flask 服务器
python app.py
```

访问 http://localhost:5000 即可使用网页界面。

### 3. 命令行使用

```bash
# 运行演示脚本
python demo.py
```

## 🐍 Anaconda 详细使用指南

### 环境管理最佳实践

```bash
# 列出所有环境
conda env list
conda info --envs

# 查看当前环境信息
conda info

# 查看环境中的包
conda list

# 更新包
conda update pandas numpy
pip install --upgrade akshare

# 导出环境配置
conda env export > environment.yml

# 从配置文件创建环境
conda env create -f environment.yml
```

### 在不同开发环境中运行

#### Anaconda Prompt（推荐新手）

1. **打开 Anaconda Prompt**
   - Windows: 开始菜单 → Anaconda3 → Anaconda Prompt
   - Linux/macOS: 打开终端

2. **激活环境并运行**
```bash
# 激活环境
conda activate stock_analysis

# 切换到项目目录
cd /path/to/your/stock-analysis

# 运行程序
python main.py
```

#### Spyder IDE（推荐数据科学）

1. **启动 Spyder**
```bash
# 在激活的环境中启动
conda activate stock_analysis
spyder
```

2. **或通过 Navigator 启动**
   - 打开 Anaconda Navigator
   - 切换到 `stock_analysis` 环境
   - 点击 Spyder 的 "Launch" 按钮

3. **在 Spyder 中运行**
   - 打开 `main.py` 文件
   - 按 F5 或点击运行按钮
   - 在控制台中查看输出

#### Jupyter Notebook（推荐交互式分析）

1. **启动 Jupyter**
```bash
conda activate stock_analysis
jupyter notebook
```

2. **创建新的 notebook**
```python
# 在 notebook 单元格中运行
%run main.py

# 或者逐步执行
from src.stock_analyzer import StockAnalyzer

analyzer = StockAnalyzer("000001")
analyzer.fetch_data()
analyzer.calculate_indicators()
analyzer.get_latest_analysis()
```

3. **使用魔法命令**
```python
# 运行外部脚本
%run src/demo.py

# 查看变量
%whos

# 测量执行时间
%time analyzer.fetch_data()
```

#### JupyterLab（现代化界面）

```bash
# 安装 JupyterLab
conda install jupyterlab -c conda-forge -y

# 启动
conda activate stock_analysis
jupyter lab
```

#### VS Code（专业开发）

1. **安装 Python 扩展**
2. **选择解释器**
   - Ctrl+Shift+P → "Python: Select Interpreter"
   - 选择 `stock_analysis` 环境的 Python

3. **配置 launch.json**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Stock Analysis",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal"
        }
    ]
}
```

### 包管理和依赖解决

#### 包冲突解决

```bash
# 查看包的依赖关系
conda list --show-channel-urls

# 解决冲突
conda update --all
conda clean --all

# 如果有冲突，创建新环境
conda create -n stock_analysis_new python=3.10
conda activate stock_analysis_new
```

#### 特定包的安装说明

**TA-Lib 安装（技术指标库）**
```bash
# Windows
pip install talib-binary

# Linux
sudo apt-get install libta-lib-dev
pip install TA-Lib

# macOS
brew install ta-lib
pip install TA-Lib
```

**akshare 网络问题解决**
```bash
# 使用国内镜像
pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 或使用阿里云镜像
pip install akshare -i https://mirrors.aliyun.com/pypi/simple/
```

### 性能优化建议

```bash
# 使用 conda-forge 频道获得更好的包
conda config --add channels conda-forge
conda config --set channel_priority strict

# 使用 mamba 加速包管理
conda install mamba -c conda-forge
mamba install pandas numpy plotly
```

## 💻 使用方法

### 网页界面使用

1. **访问应用**
   - 在浏览器中打开 http://localhost:5000
   - 支持 Chrome、Firefox、Safari、Edge 等主流浏览器

2. **输入股票代码**
   - 输入 6 位 A 股代码（如：000001）
   - 可点击示例代码快速填入
   - 支持深市（000、002、300开头）和沪市（600、601、603开头）

3. **选择时间区间**
   - 默认为过去一年的数据
   - 可自定义开始和结束日期
   - 建议选择至少 3 个月的数据以获得准确的技术指标

4. **查看分析结果**
   - 实时显示最新价格、涨跌幅
   - 技术指标分析（RSI、MACD、布林带）
   - 点击"查看详细图表"查看交互式图表

### 编程接口使用

```python
from stock_analyzer import StockAnalyzer

# 创建分析器实例
analyzer = StockAnalyzer("000001")  # 平安银行

# 获取数据（自定义时间区间）
analyzer.fetch_data("20240101", "20241231")

# 计算技术指标
analyzer.calculate_indicators()

# 获取分析结果
analysis = analyzer.get_latest_analysis()
print(analysis)

# 生成图表
analyzer.generate_chart("my_analysis.html")
```

## 📊 支持的技术指标

### 主要指标

- **MACD**（指数平滑移动平均线）
  - MACD 线：12日EMA - 26日EMA
  - 信号线：MACD的9日EMA
  - 柱状图：MACD - 信号线

- **RSI**（相对强弱指数）
  - 周期：14天
  - 超买线：70
  - 超卖线：30

- **布林带**（Bollinger Bands）
  - 中轨：20日移动平均线
  - 上轨：中轨 + 2倍标准差
  - 下轨：中轨 - 2倍标准差

### 图表类型

- **K线图**：开盘、收盘、最高、最低价格
- **成交量柱状图**：每日成交量
- **技术指标图**：MACD、RSI、布林带叠加显示

## 🎯 常用股票代码示例

### 银行股
- 000001 - 平安银行
- 600000 - 浦发银行  
- 600036 - 招商银行
- 601988 - 中国银行

### 白酒股
- 000858 - 五粮液
- 600519 - 贵州茅台
- 000568 - 泸州老窖

### 科技股
- 000002 - 万科A
- 002415 - 海康威视
- 300059 - 东方财富

## 🔧 配置说明

### Flask 应用配置

```python
# app.py 中的配置
app.run(
    debug=True,        # 开发模式
    host='0.0.0.0',   # 允许外部访问
    port=5000         # 端口号
)
```

### 数据获取配置

```python
# stock_analyzer.py 中的配置
ak.stock_zh_a_hist(
    symbol=stock_code,     # 股票代码
    period="daily",        # 日线数据
    start_date=start_date, # 开始日期
    end_date=end_date,     # 结束日期
    adjust="qfq"          # 前复权
)
```

## 🐛 常见问题

### 1. 数据获取失败
- **问题**：无法获取股票数据
- **解决**：
  - 检查网络连接
  - 确认股票代码格式正确
  - 尝试更换时间区间

### 2. 图表显示异常
- **问题**：图表无法正常显示
- **解决**：
  - 确保浏览器支持 JavaScript
  - 清除浏览器缓存
  - 尝试其他浏览器

### 3. 技术指标计算错误
- **问题**：RSI 或 MACD 显示异常
- **解决**：
  - 确保数据量足够（建议>30天）
  - 检查数据完整性
  - 重新获取数据

### 🐍 Anaconda 相关问题

#### 4. 环境激活失败
- **问题**：`conda activate` 命令不工作
- **解决**：
```bash
# 初始化 conda
conda init bash  # Linux/macOS
conda init cmd.exe  # Windows

# 重启终端或重新加载配置
source ~/.bashrc  # Linux/macOS

# 或者使用完整路径
source /path/to/anaconda3/bin/activate stock_analysis
```

#### 5. 包安装失败
- **问题**：某些包无法安装
- **解决**：
```bash
# 清理 conda 缓存
conda clean --all

# 更新 conda
conda update conda

# 使用不同的安装方法
conda install package_name -c conda-forge
# 或
pip install package_name

# 如果是网络问题，使用镜像源
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
```

#### 6. talib 安装问题
- **问题**：TA-Lib 安装失败
- **解决**：
```bash
# Windows 用户
pip install talib-binary

# Linux 用户
sudo apt-get update
sudo apt-get install build-essential
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
pip install TA-Lib

# macOS 用户
brew install ta-lib
pip install TA-Lib
```

#### 7. 环境路径问题
- **问题**：找不到 Python 解释器或模块
- **解决**：
```bash
# 检查当前环境
conda info --envs
which python
python --version

# 重新安装包到正确环境
conda activate stock_analysis
pip install --force-reinstall akshare

# 检查包安装位置
python -c "import akshare; print(akshare.__file__)"
```

#### 8. 权限问题
- **问题**：没有权限安装包
- **解决**：
```bash
# 使用用户安装
pip install --user package_name

# 或创建用户环境
conda create --prefix ./env python=3.10
conda activate ./env
```

#### 9. 内存不足
- **问题**：运行时内存不足
- **解决**：
```bash
# 限制数据获取范围
analyzer.fetch_data("20240101", "20241231")  # 只获取一年数据

# 清理不需要的变量
del analyzer.data
import gc
gc.collect()

# 使用分块处理大数据
# 在 stock_analyzer.py 中可以添加数据分块处理逻辑
```

#### 10. Jupyter Notebook 内核问题
- **问题**：Jupyter 无法找到环境
- **解决**：
```bash
# 在环境中安装 ipykernel
conda activate stock_analysis
pip install ipykernel

# 添加环境到 Jupyter
python -m ipykernel install --user --name stock_analysis --display-name "Python (Stock Analysis)"

# 启动 Jupyter 并选择正确的内核
jupyter notebook
```

#### 11. 模块导入错误
- **问题**：`ModuleNotFoundError` 错误
- **解决**：
```bash
# 检查模块是否安装
conda list | grep akshare
pip show akshare

# 重新安装问题模块
pip uninstall akshare
pip install akshare

# 检查 Python 路径
python -c "import sys; print(sys.path)"
```

#### 12. 版本冲突问题
- **问题**：包版本不兼容
- **解决**：
```bash
# 查看依赖冲突
conda env export > environment_backup.yml
conda list --explicit > spec-file.txt

# 创建新的干净环境
conda create -n stock_analysis_clean python=3.10
conda activate stock_analysis_clean

# 按顺序安装核心包
conda install pandas numpy -c conda-forge
pip install akshare plotly flask talib-binary
```

### 🔧 性能优化

#### 数据处理优化
```python
# 在 stock_analyzer.py 中使用更高效的数据处理
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('mode.chained_assignment', None)

# 使用向量化操作替代循环
self.data['returns'] = self.data['Close'].pct_change()
```

#### 内存使用优化
```python
# 指定数据类型以节省内存
dtypes = {
    'Open': 'float32',
    'Close': 'float32', 
    'High': 'float32',
    'Low': 'float32',
    'Volume': 'int64'
}
self.data = self.data.astype(dtypes)
```

## 📝 开发说明

### 核心模块

- **StockAnalyzer**: 主要分析类
  - `fetch_data()`: 数据获取
  - `calculate_indicators()`: 技术指标计算
  - `plot_analysis()`: 图表生成
  - `get_latest_analysis()`: 分析结果获取

- **Flask 路由**:
  - `/`: 主页面
  - `/analyze`: 分析接口
  - `/chart/<filename>`: 图表查看

### 扩展开发

可以通过以下方式扩展功能：

1. **添加新的技术指标**
2. **支持更多股票市场**
3. **增加数据存储功能**
4. **添加用户系统**
5. **实现股票预警功能**

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进项目！

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 创建 GitHub Issue
- 发送邮件至项目维护者

---

**⚠️ 免责声明**: 本工具仅用于技术分析学习和研究，不构成投资建议。投资有风险，入市需谨慎。 