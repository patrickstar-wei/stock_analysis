#!/bin/bash

# 股票分析系统 - 简化版前后端启动脚本
# 使用方法: bash start_system_simple.sh

echo "=== 股票分析系统 - 简化版启动脚本 ==="
echo ""

# 检查conda环境
echo "🔍 检查conda环境..."
if ! conda env list | grep -q "stock_analysis"; then
    echo "❌ 未找到stock_analysis环境，请先创建："
    echo "   conda env create -f config/environment.yml"
    exit 1
fi

echo "✅ 找到stock_analysis环境"
echo ""

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "⚠️  前端依赖未安装，正在安装..."
    cd frontend
    npm install
    cd ..
fi

echo "🚀 启动系统..."
echo ""

echo "📊 启动后端服务 (端口5000)..."
echo "   按 Ctrl+C 停止所有服务"
echo ""

# 启动后端服务
conda run -n stock_analysis python run.py &
BACKEND_PID=$!

# 等待后端启动
sleep 3

echo "🌐 启动前端服务 (端口3000)..."
echo ""

# 启动前端服务
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "⏳ 等待服务启动..."
sleep 5

echo ""
echo "🎉 系统启动完成！"
echo ""
echo "📱 访问地址:"
echo "   前端界面: http://localhost:3000"
echo "   后端API:  http://localhost:5000"
echo ""
echo "💡 使用提示:"
echo "   - 按 Ctrl+C 停止所有服务"
echo "   - 支持股票代码、公司名称、拼音缩写搜索"
echo "   - 支持日线、60分钟、30分钟、15分钟分析"
echo ""

# 等待用户中断
wait 