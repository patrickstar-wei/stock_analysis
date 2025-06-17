# 📈 股票分析系统

一个基于 Python 的专业股票分析工具，提供技术指标计算、图表生成和网页界面。

## 🚀 快速开始

### 🐍 Anaconda 环境运行（推荐）

**1. 创建 Anaconda 环境**
```bash
# 创建名为 stock_analysis 的 Python 3.10 环境
conda create -n stock_analysis python=3.10 -y

# 激活环境
conda activate stock_analysis
```

**2. 安装依赖包**
```bash
# 方法一：使用 conda 安装（推荐）
conda install pandas numpy plotly flask -c conda-forge -y
pip install akshare talib-binary

# 方法二：使用 pip 安装
pip install -r config/requirements.txt
```

**3. 运行程序**
```bash
# 交互式启动（推荐）
python main.py

# 或直接启动网页服务
python -m src.app
```

**4. 在 Anaconda Navigator 中运行**
- 打开 Anaconda Navigator
- 切换到 `stock_analysis` 环境
- 启动 Jupyter Notebook 或 Spyder
- 在 Jupyter 中运行：`%run main.py`

### 一键启动

**Linux/macOS:**
```bash
./scripts/start.sh
```

**Windows:**
```cmd
scripts\start.bat
```

### 手动启动

```bash
# 1. 安装依赖
pip install -r config/requirements.txt

# 2. 启动应用
python main.py
```

## 🐍 Anaconda 使用说明

### 环境管理

```bash
# 查看所有环境
conda env list

# 激活环境
conda activate stock_analysis

# 退出环境
conda deactivate

# 删除环境（如需要）
conda env remove -n stock_analysis
```

### 在不同 IDE 中运行

**Anaconda Prompt（命令行）:**
```bash
# 1. 打开 Anaconda Prompt
# 2. 激活环境
conda activate stock_analysis
# 3. 切换到项目目录
cd /path/to/stock-analysis
# 4. 运行程序
python main.py
```

**Spyder IDE:**
1. 打开 Anaconda Navigator
2. 选择 `stock_analysis` 环境
3. 启动 Spyder
4. 打开 `main.py` 文件
5. 点击运行按钮

**Jupyter Notebook:**
1. 在 Anaconda Navigator 中启动 Jupyter
2. 导航到项目文件夹
3. 创建新的 notebook 或打开现有文件
4. 运行代码：
```python
%run main.py
# 或
exec(open('main.py').read())
```

### 依赖包说明

| 包名 | 版本要求 | 用途 |
|------|----------|------|
| akshare | >=1.17.4 | 获取A股数据 |
| pandas | >=2.3.0 | 数据处理 |
| numpy | >=1.22.4 | 数值计算 |
| plotly | >=6.1.2 | 交互式图表 |
| flask | >=3.1.1 | 网页服务 |
| talib-binary | >=0.4.28 | 技术指标计算 |

### 🎯 快速环境配置

**使用环境配置文件（推荐）**
```bash
# 从配置文件创建环境
conda env create -f config/environment.yml

# 激活环境
conda activate stock_analysis

# 运行程序
python main.py
```

**更新现有环境**
```bash
# 激活环境
conda activate stock_analysis

# 更新环境
conda env update -f config/environment.yml
```

## 📁 项目结构

```
stock-analysis/
├── main.py                    # 主启动文件
├── README.md                  # 项目说明
├── .gitignore                 # Git 忽略文件
├── src/                       # 源代码
│   ├── __init__.py           # 包初始化
│   ├── app.py                # Flask 网页应用
│   ├── stock_analyzer.py     # 股票分析核心
│   └── demo.py               # 命令行演示
├── static/                    # 静态资源
│   └── templates/            # 网页模板
│       └── index.html        # 主页面模板
├── config/                    # 配置文件
│   ├── config.py             # 应用配置
│   └── requirements.txt      # 依赖包
├── scripts/                   # 启动脚本
│   ├── start.sh              # Linux/macOS 启动脚本
│   └── start.bat             # Windows 启动脚本
├── docs/                      # 文档
│   └── README.md             # 详细文档
└── output/                    # 输出文件
    └── *.html                # 生成的图表文件
```

## 🌟 功能特性

- 📊 **技术指标分析**：MACD、RSI、布林带等经典指标
- 📈 **交互式图表**：专业 K 线图和技术指标图表，消除周末空缺显示连续图表
- ⏰ **多时间周期**：支持日线、60分钟、30分钟、15分钟等多种时间周期分析
- 💰 **筹码峰分析**：智能计算筹码分布，显示主力资金成本区域
- 🏷️ **股票名称显示**：自动获取并显示股票中文名称
- 🌐 **网页界面**：现代化响应式设计，显示详细股票信息
- ⏰ **时间区间选择**：灵活的自定义分析时间范围
- 🔄 **实时数据**：基于 akshare 的 A 股数据
- 📱 **移动端适配**：完美支持移动设备

## 📊 使用方法

1. **网页界面**：选择模式 1，访问 http://localhost:8080
   - 选择股票代码（如：000001）
   - 选择时间周期（日线/60分钟/30分钟/15分钟）
   - 设置分析时间范围
   - 查看技术指标和筹码峰分析
2. **命令行**：选择模式 2，在终端中进行分析

## 🎯 常用股票代码

- **银行股**：000001(平安银行)、600036(招商银行)
- **白酒股**：000858(五粮液)、600519(贵州茅台)
- **科技股**：000002(万科A)、002415(海康威视)

## 📝 详细文档

- 📖 [详细文档](docs/README.md) - 了解更多功能和使用方法
- 🔧 [故障排除指南](docs/troubleshooting.md) - 常见问题解决方案

## ⚠️ 常见问题

### 端口占用
如果遇到端口占用错误，可以：
1. 更改端口号（在 `src/app.py` 中修改）
2. 停止占用端口的程序
3. 查看 [故障排除指南](docs/troubleshooting.md) 获取详细解决方案

### 模板文件找不到
确保项目文件结构正确，特别是 `static/templates/index.html` 文件存在。

### 依赖包问题
使用 `conda activate stock_analysis` 激活环境后再安装依赖包。

## 🧪 快速测试

**在 Cursor 中测试应用：**
```bash
# 启动应用后，在另一个终端运行测试
conda activate stock_analysis
python scripts/test_app.py
```

此脚本会：
- ✅ 检查所有依赖包是否安装
- ✅ 测试多个端口的连接性
- ✅ 验证页面内容和功能
- ✅ 提供详细的诊断信息

## 🔧 开发说明

### 核心模块
- `src/stock_analyzer.py`：股票数据分析核心
- `src/app.py`：Flask 网页应用
- `src/demo.py`：命令行演示

### 配置文件
- `config/config.py`：应用配置参数
- `config/requirements.txt`：项目依赖

### 启动方式
- 交互式：`python main.py`
- 直接启动网页：`python -m src.app`
- 命令行演示：`python -m src.demo`

## ⚠️ 免责声明

本工具仅用于技术分析学习和研究，不构成投资建议。投资有风险，入市需谨慎。 