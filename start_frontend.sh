#!/bin/bash

echo "=== 启动股票分析系统前端 ==="
echo "正在进入前端目录..."

cd frontend

echo "检查依赖包..."
if [ ! -d "node_modules" ]; then
    echo "安装依赖包..."
    npm install
fi

echo "启动React开发服务器..."
echo "前端将在 http://localhost:3000 启动"
echo "按 Ctrl+C 停止服务器"
echo ""

npm start 