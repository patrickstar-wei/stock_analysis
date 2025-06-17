#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
股票分析系统主启动文件
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """主函数"""
    print("=== 股票分析系统 ===")
    print("1. 启动网页服务器")
    print("2. 运行命令行演示")
    print("3. 退出")
    
    while True:
        choice = input("\n请选择运行模式 (1-3): ").strip()
        
        if choice == '1':
            print("\n启动网页服务器...")
            print("请在浏览器中访问: http://localhost:8080")
            print("按 Ctrl+C 停止服务器\n")
            
            # 直接运行 Flask 应用，避免导入冲突
            import subprocess
            import sys
            try:
                subprocess.run([sys.executable, 'src/app.py'], check=True)
            except KeyboardInterrupt:
                print("\n服务器已停止")
            except subprocess.CalledProcessError as e:
                print(f"启动服务器失败: {e}")
            break
            
        elif choice == '2':
            print("\n运行命令行演示...")
            from src.demo import demo as demo_main
            demo_main()
            break
            
        elif choice == '3':
            print("退出程序")
            break
            
        else:
            print("无效选择，请输入 1-3")

if __name__ == '__main__':
    main() 