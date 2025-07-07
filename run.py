#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
股票分析系统启动脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """启动Flask应用"""
    print("=== 股票分析系统 ===")
    print("启动Flask应用...")
    print("请在浏览器中访问: http://localhost:5000")
    print("按 Ctrl+C 停止服务器\n")
    
    try:
        from src.app import app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        print("请确保已激活stock_analysis环境: conda activate stock_analysis")

if __name__ == '__main__':
    main() 