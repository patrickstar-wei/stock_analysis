from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import json

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analysis.stock_analyzer import StockAnalyzer

# 创建Flask应用（只提供API服务，不渲染模板）
app = Flask(__name__)

# 启用CORS支持
CORS(app, resources={r"/*": {"origins": "*"}})

# 递归转换numpy类型为原生类型
def convert_np(obj):
    if isinstance(obj, dict):
        return {k: convert_np(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_np(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

@app.route('/')
def index():
    """API服务状态检查"""
    return jsonify({
        'success': True,
        'message': '股票分析系统API服务运行正常',
        'version': '1.0.0',
        'endpoints': [
            '/search_stocks - 搜索股票',
            '/get_stock_info - 获取股票信息',
            '/trading_signals - 获取交易信号'
        ]
    })



@app.route('/trading_signals', methods=['POST'])
def get_trading_signals():
    """获取多周期交易信号分析"""
    try:
        # 获取JSON数据
        data = request.get_json()
        stock_input = data.get('stock_code', '000001').strip() if data else '000001'
        
        # 定义所有时间周期
        time_periods = {
            'weekly': '周线',
            'daily': '日线', 
            '60': '60分钟',
            '30': '30分钟',
            '15': '15分钟'
        }
        
        # 使用默认时间范围（最近三年，约1095天）
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=1095)).strftime('%Y-%m-%d')
        
        # 直接使用输入的股票代码
        stock_code = stock_input
        stock_name = None
        
        # 转换日期格式
        try:
            start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y%m%d')
            end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y%m%d')
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': f'日期格式错误: {e}'
            })
        
        print(f"获取多周期交易信号: {stock_code}, 时间范围: {start_date_formatted} - {end_date_formatted}")
        
        # 存储所有周期的分析结果
        all_signals = {}
        all_stock_data = {}
        period_dfs = {}
        stock_info = None
        
        # 为每个时间周期生成分析
        for period_key, period_name in time_periods.items():
            try:
                print(f"分析 {period_name} 周期...")
                
                # 创建分析器实例
                analyzer = StockAnalyzer(stock_code)
                
                # 获取数据
                if not analyzer.fetch_data(start_date_formatted, end_date_formatted, period_key):
                    print(f"无法获取 {period_name} 数据")
                    continue
                
                # 计算技术指标
                analyzer.calculate_indicators()
                
                # 生成交易信号
                signals = analyzer.generate_trading_signals()
                
                if signals is None:
                    print(f"{period_name} 数据不足，无法生成交易信号")
                    continue
                
                # 存储信号
                all_signals[period_key] = {
                    'period_name': period_name,
                    'signals': convert_np(signals)
                }
                
                # 准备股票数据用于前端图表（只保留最近100条记录以提高性能）
                stock_data = []
                if analyzer.data is not None and len(analyzer.data) > 0:
                    # 只取最近100条记录
                    recent_data = analyzer.data.tail(100)
                    for _, row in recent_data.iterrows():
                        stock_data.append({
                            'Date': row['Date'],
                            'Open': float(row['Open']),
                            'High': float(row['High']),
                            'Low': float(row['Low']),
                            'Close': float(row['Close']),
                            'Volume': float(row['Volume'])
                        })
                
                all_stock_data[period_key] = stock_data
                
                # 存储完整 DataFrame 用于回测
                period_dfs[period_key] = analyzer.data.copy()
                
                # 保存股票信息（使用第一个成功的结果）
                if stock_info is None:
                    stock_info = {
                        'code': stock_code,
                        'name': analyzer.stock_name or stock_name,
                        'sector': '',
                        'market': 'A股'
                    }
                
            except Exception as e:
                print(f"分析 {period_name} 周期失败: {e}")
                continue
        
        if not all_signals:
            return jsonify({
                'success': False,
                'message': f'无法获取股票 {stock_code} 的任何周期数据，请检查股票代码是否正确'
            })
        
        # 生成综合建议
        comprehensive_advice = generate_comprehensive_advice(all_signals)
        
        # ---------- 回测结果 ----------
        backtest_result = generate_backtest_result(period_dfs)
        
        return jsonify({
            'success': True,
            'message': f'成功生成 {stock_info["name"]}({stock_code}) 的多周期交易信号',
            'all_signals': all_signals,
            'all_stock_data': all_stock_data,
            'stock_info': stock_info,
            'comprehensive_advice': comprehensive_advice,
            'backtest_result': backtest_result
        })
        
    except Exception as e:
        print(f"获取交易信号失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取交易信号失败: {str(e)}'
        })

def generate_comprehensive_advice(all_signals):
    """生成综合买卖建议"""
    buy_count = 0
    sell_count = 0
    hold_count = 0
    total_periods = len(all_signals)
    
    # 统计各周期的信号
    period_analysis = {}
    for period_key, period_data in all_signals.items():
        signals = period_data['signals']
        signal_type = signals.get('signal_type', '')
        
        if '买入' in signal_type:
            buy_count += 1
        elif '卖出' in signal_type:
            sell_count += 1
        else:
            hold_count += 1
        
        period_analysis[period_key] = {
            'period_name': period_data['period_name'],
            'signal_type': signal_type,
            'signal_strength': signals.get('signal_strength', ''),
            'risk_level': signals.get('risk_level', '中')
        }
    
    # 生成综合建议
    if buy_count > sell_count and buy_count > hold_count:
        overall_signal = '买入'
        signal_strength = '强' if buy_count >= 3 else '中等'
        advice = f'在{total_periods}个时间周期中，{buy_count}个周期显示买入信号，建议考虑买入。'
    elif sell_count > buy_count and sell_count > hold_count:
        overall_signal = '卖出'
        signal_strength = '强' if sell_count >= 3 else '中等'
        advice = f'在{total_periods}个时间周期中，{sell_count}个周期显示卖出信号，建议考虑卖出。'
    else:
        overall_signal = '观望'
        signal_strength = '中等'
        advice = f'各时间周期信号不一致，建议观望等待更明确的信号。'
    
    return {
        'overall_signal': overall_signal,
        'signal_strength': signal_strength,
        'advice': advice,
        'statistics': {
            'total_periods': total_periods,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'hold_count': hold_count
        },
        'period_analysis': period_analysis
    }



@app.route('/search_stocks', methods=['GET'])
def search_stocks():
    """搜索股票API"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({
                'success': True,
                'stocks': []
            })
        
        # 使用akshare获取股票信息
        try:
            import akshare as ak
            
            # 获取A股股票列表
            stock_list = ak.stock_info_a_code_name()
            
            results = []
            query_lower = query.lower()
            
            # 搜索匹配的股票
            for _, row in stock_list.iterrows():
                code = str(row['code']).strip()
                name = str(row['name']).strip()
                
                # 匹配股票代码或公司名称
                if (query_lower in code.lower() or 
                    query_lower in name.lower() or
                    code.startswith(query) or
                    name.startswith(query)):
                    
                    results.append({
                        'code': code,
                        'name': name,
                        'sector': '',  # 可以后续添加行业信息
                        'market': 'A股'
                    })
                    
                    # 限制返回数量
                    if len(results) >= limit:
                        break
            
            return jsonify({
                'success': True,
                'stocks': results
            })
            
        except Exception as e:
            print(f"akshare获取股票列表失败: {e}")
            # 回退到简单实现
            results = []
            if query:
                if any(char.isdigit() for char in query):
                    results.append({
                        'code': query,
                        'name': f'股票{query}',
                        'sector': '',
                        'market': 'A股'
                    })
                else:
                    results.append({
                        'code': '000001',
                        'name': '平安银行',
                        'sector': '银行',
                        'market': 'A股'
                    })
            return jsonify({
                'success': True,
                'stocks': results
            })
        
    except Exception as e:
        print(f"搜索股票失败: {e}")
        return jsonify({
            'success': False,
            'message': f'搜索失败: {str(e)}',
            'stocks': []
        })

@app.route('/get_stock_info', methods=['GET'])
def get_stock_info():
    """获取股票信息API"""
    try:
        code_or_name = request.args.get('code_or_name', '').strip()
        
        if not code_or_name:
            return jsonify({
                'success': False,
                'message': '请提供股票代码或公司名称'
            })
        
        # 使用akshare获取股票信息
        try:
            import akshare as ak
            
            # 获取A股股票列表
            stock_list = ak.stock_info_a_code_name()
            
            # 查找匹配的股票
            for _, row in stock_list.iterrows():
                code = str(row['code']).strip()
                name = str(row['name']).strip()
                
                # 匹配股票代码或公司名称
                if (code_or_name == code or 
                    code_or_name.lower() in name.lower() or
                    code.startswith(code_or_name) or
                    name.startswith(code_or_name)):
                    
                    # 尝试获取更多股票信息
                    try:
                        stock_info = ak.stock_individual_info_em(symbol=code)
                        sector = ''
                        if not stock_info.empty:
                            industry_rows = stock_info[stock_info['item'].str.contains('行业', na=False)]
                            if not industry_rows.empty:
                                sector = industry_rows.iloc[0]['value']
                    except:
                        sector = ''
                    
                    stock_info = {
                        'code': code,
                        'name': name,
                        'sector': sector,
                        'market': 'A股'
                    }
                    return jsonify({
                        'success': True,
                        'stock': stock_info
                    })
            
            # 如果没找到，返回默认信息
            stock_info = {
                'code': code_or_name,
                'name': f'股票{code_or_name}',
                'sector': '',
                'market': 'A股'
            }
            return jsonify({
                'success': True,
                'stock': stock_info
            })
            
        except Exception as e:
            print(f"akshare获取股票信息失败: {e}")
            # 回退到简单实现
            stock_info = {
                'code': code_or_name,
                'name': f'股票{code_or_name}',
                'sector': '',
                'market': 'A股'
            }
            return jsonify({
                'success': True,
                'stock': stock_info
            })
        
    except Exception as e:
        print(f"获取股票信息失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取股票信息失败: {str(e)}'
        })

# --------------------------------------------------------------------------------------
# 回测逻辑（简化版本：基于 MACD 多周期权重策略）
# --------------------------------------------------------------------------------------
from src.analysis.indicators import TechnicalIndicators
import numpy as np


def _macd_position(macd: np.ndarray, signal: np.ndarray):
    """根据 MACD 与 signal 线判断持仓（1 持有 / 0 空仓）。"""
    if len(macd) != len(signal):
        return np.zeros(len(macd))
    pos = np.zeros(len(macd))
    for i in range(1, len(macd)):
        if macd[i - 1] <= signal[i - 1] and macd[i] > signal[i]:  # 金叉
            pos[i] = 1
        elif macd[i - 1] >= signal[i - 1] and macd[i] < signal[i]:  # 死叉
            pos[i] = 0
        else:
            pos[i] = pos[i - 1]
    return pos


def backtest_macd_strategy(df):
    """对单一周期 DataFrame 进行 MACD 策略回测，返回收益率和交易明细。"""
    if df is None or df.empty or 'Close' not in df.columns:
        return {
            'return_pct': 0.0,
            'trades': []
        }

    macd_dict = TechnicalIndicators.calculate_macd(df['Close'])
    macd = macd_dict['macd'].values
    signal = macd_dict['signal'].values

    # 对齐长度
    valid_len = min(len(macd), len(signal), len(df))
    macd = macd[-valid_len:]
    signal = signal[-valid_len:]
    closes = df['Close'].values[-valid_len:]
    dates = df['Date'].values[-valid_len:]

    pos = np.zeros(valid_len)
    trades = []
    holding_price = None
    last_trade_day = None  # 记录上一次交易发生的日期 (YYYY-MM-DD)

    def _same_day(ts1, ts2):
        """判断两个时间戳是否属于同一天"""
        d1 = pd.to_datetime(ts1).strftime('%Y-%m-%d')
        d2 = pd.to_datetime(ts2).strftime('%Y-%m-%d')
        return d1 == d2

    for i in range(1, valid_len):
        current_day = pd.to_datetime(dates[i]).strftime('%Y-%m-%d')

        # 如果本日已经发生过交易，直接沿用上一时刻仓位
        if last_trade_day == current_day:
            pos[i] = pos[i - 1]
            continue

        # 金叉 -> 买入
        if macd[i - 1] <= signal[i - 1] and macd[i] > signal[i]:
            pos[i] = 1
            holding_price = closes[i]
            trades.append({
                'type': 'buy',
                'date': str(dates[i]),
                'price': float(closes[i])
            })
            last_trade_day = current_day

        # 死叉 -> 卖出
        elif macd[i - 1] >= signal[i - 1] and macd[i] < signal[i]:
            pos[i] = 0
            if holding_price is not None:
                profit_pct = (closes[i] - holding_price) / holding_price
                trades.append({
                    'type': 'sell',
                    'date': str(dates[i]),
                    'price': float(closes[i]),
                    'profit_pct': round(profit_pct * 100, 2),
                    'profit_amount': round((closes[i] - holding_price), 2)
                })
                holding_price = None
            last_trade_day = current_day
        else:
            pos[i] = pos[i - 1]

    # 计算整体收益率
    pct_change = np.append([0], np.diff(closes) / closes[:-1])
    strategy_ret = (pos[:-1] * pct_change[1:]).sum()

    return {
        'return_pct': strategy_ret,
        'trades': trades
    }


def generate_backtest_result(period_dfs: dict):
    """仅使用日线 DataFrame 生成 MACD 策略回测结果。"""
    if 'daily' not in period_dfs or period_dfs['daily'] is None or period_dfs['daily'].empty:
        return {
            'capital_start': 1_000_000,
            'capital_end': 1_000_000,
            'total_return_pct': 0.0,
            'profit_amount': 0.0,
            'details': {}
        }

    df_daily = period_dfs['daily']
    result = backtest_macd_strategy(df_daily)
    total_ret = result['return_pct']
    trades = result['trades']

    capital_start = 1_000_000
    capital_end = capital_start * (1 + total_ret)
    profit_amount = capital_end - capital_start

    details = {
        'daily': {
            'period_name': '日线',
            'return_pct': round(total_ret * 100, 2),
            'trades': trades
        }
    }

    # ------------------ 生成每笔交易时各周期决策 ------------------
    def macd_signal_type(close_series):
        """根据给定收盘价序列计算MACD信号类型（强烈买入/买入/卖出/强烈卖出/观望）"""
        if len(close_series) < 35:  # 至少有足够数据计算EMA
            return '观望'
        macd_dict_ = TechnicalIndicators.calculate_macd(close_series)
        macd_line = macd_dict_['macd'].iloc[-1]
        signal_line = macd_dict_['signal'].iloc[-1]
        diff = macd_line - signal_line
        if diff > 0:
            if diff > abs(signal_line) * 0.3:
                return '强烈买入'
            return '买入'
        elif diff < 0:
            if abs(diff) > abs(signal_line) * 0.3:
                return '强烈卖出'
            return '卖出'
        return '观望'

    # 需要的周期列表（如存在于period_dfs中）
    decision_periods = ['15', '30', '60', 'daily', 'weekly']

    for trade in trades:
        trade_dt = pd.to_datetime(trade['date'])
        # 当日结束时间（次日零点），用于包含当天所有收盘前数据
        day_end = (trade_dt.floor('D') + pd.Timedelta(days=1))
        decisions = []
        for p in decision_periods:
            df_p = period_dfs.get(p)
            if df_p is None or df_p.empty:
                continue
            # 取在 day_end 之前的所有数据，确保包含当日全部bar（收盘价）
            df_slice = df_p[df_p['Date'] < day_end]
            if df_slice.empty:
                continue
            sig_type = macd_signal_type(df_slice['Close'])
            decisions.append({
                'period': p,
                'signal_type': sig_type
            })
        trade['decisions'] = decisions

    return {
        'capital_start': capital_start,
        'capital_end': round(capital_end, 2),
        'total_return_pct': round(total_ret * 100, 2),
        'profit_amount': round(profit_amount, 2),
        'details': details
    }

# ------------------ 回测权重配置 ------------------
def load_backtest_weights():
    """从 config/backtest_weights.json 读取各周期回测权重。若文件不存在或格式错误，返回默认权重。"""
    default_weights = {
        '15': 1,
        '30': 3,
        '60': 2,
        'daily': 3,
        'weekly': 1,
    }

    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, 'config', 'backtest_weights.json')
        if not os.path.isfile(config_path):
            print(f"找不到回测权重配置文件 {config_path}，使用默认权重")
            return default_weights

        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            print("回测权重配置格式错误，使用默认权重")
            return default_weights

        # 只保留需要的键，且确保值为数字
        weights = {}
        for k, v in data.items():
            try:
                weights[str(k)] = float(v)
            except (TypeError, ValueError):
                print(f"回测权重配置中 {k}:{v} 非数字，忽略")

        # 如果配置为空则返回默认
        return weights if weights else default_weights
    except Exception as e:
        print(f"读取回测权重配置失败: {e}，使用默认权重")
        return default_weights

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 