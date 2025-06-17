#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
股票分析系统快速测试脚本
用于在 Cursor 中测试 Flask 应用是否正常运行
"""

import requests
import time
import sys
import os

def test_flask_app(port=8080, timeout=30):
    """
    测试 Flask 应用是否正常运行
    
    Args:
        port (int): 应用端口号
        timeout (int): 超时时间（秒）
    """
    url = f"http://localhost:{port}"
    
    print("🔍 正在测试股票分析系统...")
    print(f"📍 测试地址: {url}")
    print("⏳ 等待应用启动...")
    
    # 等待应用启动
    time.sleep(3)
    
    try:
        print("🌐 发送HTTP请求...")
        response = requests.get(url, timeout=timeout)
        
        print(f"📊 状态码: {response.status_code}")
        print(f"📏 响应长度: {len(response.text)} 字符")
        
        if response.status_code == 200:
            print("✅ Flask 应用正常运行！")
            
            # 检查页面内容
            if "股票分析系统" in response.text:
                print("✅ 页面内容正确，包含预期标题")
            else:
                print("⚠️ 页面内容可能有问题，未找到预期标题")
                
            # 检查关键元素
            checks = [
                ("表单元素", "stock_code"),
                ("提交按钮", "submit"),
                ("日期选择", "start_date"),
                ("样式表", "<style>"),
                ("JavaScript", "<script>")
            ]
            
            print("\n🔍 检查页面元素:")
            for name, element in checks:
                if element in response.text:
                    print(f"  ✅ {name}: 存在")
                else:
                    print(f"  ❌ {name}: 缺失")
            
            print(f"\n🎉 测试完成！请在浏览器中访问: {url}")
            return True
            
        elif response.status_code == 500:
            print("❌ 服务器内部错误 (500)")
            print("💡 可能的原因:")
            print("  - 模板文件路径错误")
            print("  - 依赖包缺失")
            print("  - 代码语法错误")
            return False
            
        else:
            print(f"❌ 意外的状态码: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 Flask 应用")
        print("💡 可能的原因:")
        print(f"  - 应用未在端口 {port} 上运行")
        print("  - 端口被其他程序占用")
        print("  - 应用启动失败")
        print("\n🔧 建议操作:")
        print("  1. 检查应用是否正在运行")
        print("  2. 尝试不同的端口号")
        print("  3. 查看应用启动日志")
        return False
        
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时 ({timeout}秒)")
        print("💡 可能的原因:")
        print("  - 应用响应缓慢")
        print("  - 网络连接问题")
        return False
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

def check_dependencies():
    """检查必要的依赖包"""
    print("📦 检查依赖包...")
    
    required_packages = [
        'requests',
        'flask', 
        'akshare',
        'pandas',
        'numpy',
        'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}: 已安装")
        except ImportError:
            print(f"  ❌ {package}: 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ 缺少依赖包: {', '.join(missing_packages)}")
        print("🔧 请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有依赖包已安装")
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("🧪 股票分析系统快速测试")
    print("=" * 50)
    
    # 检查依赖包
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请先安装缺少的包")
        sys.exit(1)
    
    print()
    
    # 测试不同端口
    ports = [8080, 5000, 5001, 8000]
    
    for port in ports:
        print(f"\n🔍 测试端口 {port}...")
        if test_flask_app(port, timeout=10):
            break
        print(f"端口 {port} 测试失败，尝试下一个端口...")
    else:
        print("\n❌ 所有端口测试失败")
        print("\n🔧 故障排除建议:")
        print("1. 确认 Flask 应用正在运行")
        print("2. 检查端口是否被占用")
        print("3. 查看应用启动日志")
        print("4. 参考故障排除指南: docs/troubleshooting.md")
        sys.exit(1)

if __name__ == "__main__":
    main() 