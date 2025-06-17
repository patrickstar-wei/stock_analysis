from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
from datetime import datetime, timedelta
import numpy as np

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_analyzer import StockAnalyzer
import json

# 设置模板和静态文件路径
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'templates')
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """分析股票数据"""
    try:
        # 获取表单数据
        stock_code = request.form.get('stock_code', '000001')
        start_date = request.form.get('start_date', '2022-01-01')
        end_date = request.form.get('end_date', '2025-12-31')
        time_period = request.form.get('time_period', 'daily')  # 新增时间周期参数
        
        # 转换日期格式：从 YYYY-MM-DD 转换为 YYYYMMDD
        try:
            from datetime import datetime
            start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y%m%d')
            end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y%m%d')
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': f'日期格式错误: {e}'
            })
        
        # 获取时间周期名称
        period_names = {
            'daily': '日线',
            '60': '60分钟',
            '30': '30分钟',
            '15': '15分钟'
        }
        period_name = period_names.get(time_period, '日线')
        
        print(f"分析股票: {stock_code}, 时间范围: {start_date_formatted} - {end_date_formatted}, 周期: {period_name}")
        
        # 创建分析器实例
        analyzer = StockAnalyzer(stock_code)
        
        # 获取数据
        if not analyzer.fetch_data(start_date_formatted, end_date_formatted, time_period):
            return jsonify({
                'success': False,
                'message': f'无法获取股票 {stock_code} 的{period_name}数据，请检查股票代码是否正确'
            })
        
        # 计算技术指标
        analyzer.calculate_indicators()
        
        # 生成图表
        fig = analyzer.plot_analysis()
        
        # 保存图表为HTML
        filename = f"{stock_code}_{time_period}_analysis.html"
        filepath = os.path.join('output', filename)
        
        # 确保输出目录存在
        os.makedirs('output', exist_ok=True)
        
        # 保存图表
        fig.write_html(filepath, config={'displayModeBar': True})
        
        # 获取基本统计信息
        latest_data = analyzer.data.iloc[-1]
        stock_name = analyzer.stock_name if analyzer.stock_name else f"股票{stock_code}"
        
        # 筹码峰分析
        chip_analysis = ""
        if analyzer.chip_data is not None:
            latest_chips = analyzer.chip_data['chip_distribution'][-1]
            price_range = analyzer.chip_data['price_range']
            
            # 找到主要筹码峰
            max_chip_idx = np.argmax(latest_chips)
            main_chip_price = price_range[max_chip_idx]
            current_price = float(latest_data['Close'])
            
            if current_price > main_chip_price * 1.05:
                chip_analysis = "价格高于主筹码峰，可能面临压力"
            elif current_price < main_chip_price * 0.95:
                chip_analysis = "价格低于主筹码峰，可能获得支撑"
            else:
                chip_analysis = "价格在主筹码峰附近，关注突破方向"
        
        stats = {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'time_period': period_name,
            'latest_price': float(latest_data['Close']),
            'latest_date': latest_data['Date'].strftime('%Y-%m-%d %H:%M' if time_period != 'daily' else '%Y-%m-%d'),
            'price_change': float(latest_data['Close'] - analyzer.data.iloc[-2]['Close']) if len(analyzer.data) > 1 else 0,
            'volume': int(latest_data['Volume']),
            'rsi': float(latest_data['RSI']),
            'macd': float(latest_data['MACD']),
            'data_points': len(analyzer.data),
            'chip_analysis': chip_analysis
        }
        
        return jsonify({
            'success': True,
            'message': f'成功分析股票 {stock_name}({stock_code}) {period_name}数据',
            'chart_file': filename,
            'stats': stats
        })
        
    except Exception as e:
        print(f"分析失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'分析失败: {str(e)}'
        })

@app.route('/chart/<filename>')
def view_chart(filename):
    """查看图表文件"""
    try:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
        chart_path = os.path.join(output_dir, filename)
        return send_file(chart_path, as_attachment=False)
    except FileNotFoundError:
        return "图表文件未找到", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080) 