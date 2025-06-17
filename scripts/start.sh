#!/bin/bash

echo "=== 股票分析系统启动脚本 ==="

# 获取脚本所在目录的父目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 检查是否安装了 conda
if ! command -v conda &> /dev/null; then
    echo "❌ 错误: 未找到 conda 命令"
    echo "请先安装 Anaconda 或 Miniconda："
    echo "  - Anaconda: https://www.anaconda.com/products/distribution"
    echo "  - Miniconda: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# 初始化 conda（如果需要）
if [[ "$SHELL" == *"bash"* ]]; then
    source $(conda info --base)/etc/profile.d/conda.sh
elif [[ "$SHELL" == *"zsh"* ]]; then
    source $(conda info --base)/etc/profile.d/conda.sh
fi

# 检查是否存在 conda 环境
echo "🔍 检查 conda 环境..."
if ! conda info --envs | grep -q "stock_analysis"; then
    echo "📦 正在创建 conda 环境 'stock_analysis'..."
    conda create -n stock_analysis python=3.10 -y
    if [ $? -ne 0 ]; then
        echo "❌ 创建环境失败"
        exit 1
    fi
    echo "✅ 环境创建成功"
else
    echo "✅ 环境 'stock_analysis' 已存在"
fi

# 激活环境
echo "🔄 激活 conda 环境..."
conda activate stock_analysis
if [ $? -ne 0 ]; then
    echo "❌ 激活环境失败，尝试使用完整路径..."
    source $(conda info --base)/bin/activate stock_analysis
    if [ $? -ne 0 ]; then
        echo "❌ 无法激活环境，请手动执行："
        echo "  conda activate stock_analysis"
        exit 1
    fi
fi

# 验证 Python 版本
echo "🐍 验证 Python 环境..."
python_version=$(python --version 2>&1)
echo "当前 Python 版本: $python_version"

# 检查并安装依赖
echo "📋 检查依赖包..."
if [ -f "config/requirements.txt" ]; then
    echo "正在安装/更新依赖包..."
    
    # 先尝试用 conda 安装主要包
    echo "使用 conda 安装主要包..."
    conda install pandas numpy plotly flask -c conda-forge -y
    
    # 再用 pip 安装其他包
    echo "使用 pip 安装其他包..."
    pip install -r config/requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "⚠️  某些包安装可能失败，但会尝试继续运行"
    else
        echo "✅ 依赖包安装完成"
    fi
else
    echo "⚠️  未找到 requirements.txt 文件"
fi

# 检查关键包是否可用
echo "🔍 验证关键包..."
python -c "import akshare, pandas, numpy, plotly, flask; print('✅ 所有关键包导入成功')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  某些关键包可能未正确安装，但会尝试运行"
fi

# 创建输出目录
mkdir -p output

# 启动应用
echo ""
echo "🚀 启动股票分析系统..."
echo "项目路径: $PROJECT_ROOT"
echo "Python 环境: $(which python)"
echo ""

python main.py 