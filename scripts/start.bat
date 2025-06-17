@echo off
echo === 股票分析系统启动脚本 ===
echo.

REM 切换到项目根目录
cd /d "%~dp0.."

REM 检查是否安装了 conda
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 conda 命令
    echo 请先安装 Anaconda 或 Miniconda:
    echo   - Anaconda: https://www.anaconda.com/products/distribution
    echo   - Miniconda: https://docs.conda.io/en/latest/miniconda.html
    echo.
    pause
    exit /b 1
)

REM 检查是否存在 conda 环境
echo 🔍 检查 conda 环境...
conda info --envs | findstr "stock_analysis" >nul
if %errorlevel% neq 0 (
    echo 📦 正在创建 conda 环境 'stock_analysis'...
    conda create -n stock_analysis python=3.10 -y
    if %errorlevel% neq 0 (
        echo ❌ 创建环境失败
        pause
        exit /b 1
    )
    echo ✅ 环境创建成功
) else (
    echo ✅ 环境 'stock_analysis' 已存在
)

REM 激活环境
echo 🔄 激活 conda 环境...
call conda activate stock_analysis
if %errorlevel% neq 0 (
    echo ❌ 激活环境失败，请手动执行:
    echo   conda activate stock_analysis
    pause
    exit /b 1
)

REM 验证 Python 版本
echo 🐍 验证 Python 环境...
python --version
echo.

REM 检查并安装依赖
echo 📋 检查依赖包...
if exist "config\requirements.txt" (
    echo 正在安装/更新依赖包...
    
    REM 先尝试用 conda 安装主要包
    echo 使用 conda 安装主要包...
    conda install pandas numpy plotly flask -c conda-forge -y
    
    REM 再用 pip 安装其他包
    echo 使用 pip 安装其他包...
    pip install -r config\requirements.txt
    
    if %errorlevel% neq 0 (
        echo ⚠️  某些包安装可能失败，但会尝试继续运行
    ) else (
        echo ✅ 依赖包安装完成
    )
) else (
    echo ⚠️  未找到 requirements.txt 文件
)

REM 检查关键包是否可用
echo 🔍 验证关键包...
python -c "import akshare, pandas, numpy, plotly, flask; print('✅ 所有关键包导入成功')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  某些关键包可能未正确安装，但会尝试运行
)

REM 创建输出目录
if not exist "output" mkdir output

REM 启动应用
echo.
echo 🚀 启动股票分析系统...
echo 项目路径: %CD%
echo Python 环境: 
where python
echo.

python main.py

pause 