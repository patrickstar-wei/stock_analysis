#!/bin/bash

# 股票分析系统 - 前后端同时启动脚本
# 使用方法: ./start_system.sh

set -e  # 遇到错误时退出

echo "=== 股票分析系统 - 前后端启动脚本 ==="
echo ""

# 检查conda是否安装
if ! command -v conda &> /dev/null; then
    echo "❌ 错误: 未找到conda命令，请先安装Anaconda或Miniconda"
    exit 1
fi

# 检查stock_analysis环境是否存在
if ! conda env list | grep -q "stock_analysis"; then
    echo "❌ 错误: 未找到stock_analysis环境"
    echo "请先创建环境: conda env create -f config/environment.yml"
    exit 1
fi

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "⚠️  前端依赖未安装，正在安装..."
    cd frontend
    npm install
    cd ..
fi

echo "🚀 正在启动股票分析系统..."
echo ""

# 激活conda环境
source ~/anaconda3/etc/profile.d/conda.sh
conda activate stock_analysis

# 启动后端服务
printf '\n📊 启动后端服务...\n'
nohup python src/app.py > backend.log 2>&1 &
BACKEND_PID=$!

# 检查后端是否启动成功
sleep 3
if ! nc -z localhost 5000; then
  echo "❌ 后端服务启动失败"
  tail -20 backend.log
  kill $BACKEND_PID 2>/dev/null
  exit 1
fi

printf '\n✅ 后端服务已启动: http://localhost:5000\n'

# 启动前端服务
printf '\n🌐 启动前端服务...\n'
cd frontend
nohup npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

sleep 5
if ! nc -z localhost 3000; then
  echo "❌ 前端服务启动失败"
  tail -20 frontend.log
  kill $FRONTEND_PID 2>/dev/null
  kill $BACKEND_PID 2>/dev/null
  exit 1
fi

printf '\n✅ 前端服务已启动: http://localhost:3000\n'

printf '\n🎉 股票分析系统启动完成！\n'
printf '\n📱 访问地址:\n   前端界面: http://localhost:3000\n   后端API:  http://localhost:5000\n'
printf '\n按 Ctrl+C 停止所有服务\n'

# 等待用户中断
trap 'echo; echo "🛑 正在停止所有服务..."; kill $FRONTEND_PID $BACKEND_PID 2>/dev/null; echo "✅ 服务已停止"; exit 0' SIGINT
wait
