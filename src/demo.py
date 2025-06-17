#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.stock_analyzer import StockAnalyzer

def demo():
    """演示股票分析功能"""
    print("=== 股票分析演示 ===")
    
    # 使用平安银行(000001)作为示例
    stock_code = "000001"
    print(f"正在分析股票: {stock_code} (平安银行)")
    
    # 创建分析器
    analyzer = StockAnalyzer(stock_code)
    
    # 获取数据
    print("正在获取股票数据...")
    if not analyzer.fetch_data():
        print("获取数据失败")
        return
    
    # 计算技术指标
    print("正在计算技术指标...")
    if not analyzer.calculate_indicators():
        print("计算指标失败")
        return
    
    # 显示最新分析结果
    analyzer.get_latest_signals()
    
    # 生成图表
    print("\n正在生成分析图表...")
    fig = analyzer.plot_analysis()
    
    if fig:
        # 在浏览器中显示图表
        fig.show()
        
        # 保存为HTML文件
        filename = f"{stock_code}_analysis.html"
        fig.write_html(filename)
        print(f"图表已保存为: {filename}")
        print("您可以在浏览器中打开此文件查看详细图表")
    
    print("\n演示完成！")

if __name__ == "__main__":
    demo() 