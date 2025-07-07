"""
股票分析器主类
整合数据获取、指标计算、信号生成、图表生成等功能
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base_analyzer import BaseAnalyzer
from .indicators import TechnicalIndicators
from .signals import SignalGenerator
from .charts import ChartGenerator
from .data_fetcher import DataFetcher

class StockAnalyzer(BaseAnalyzer):
    """股票分析器主类"""
    
    def __init__(self, stock_code_or_name, period="1000"):
        """
        初始化股票分析器
        :param stock_code_or_name: A股代码或公司名称
        :param period: 获取数据的天数
        """
        super().__init__(stock_code_or_name, period)
        self.indicators = {}
        self.signals = {}
        self.chart_generator = None
        self.signal_generator = None
    
    def calculate_indicators(self):
        """计算所有技术指标"""
        if self.data is None or len(self.data) == 0:
            print("没有数据，无法计算指标")
            return False
        
        try:
            print("正在计算技术指标...")
            
            # 计算RSI
            self.indicators['rsi'] = TechnicalIndicators.calculate_rsi(
                self.data['Close'], period=14
            )
            
            # 计算布林带
            upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(
                self.data['Close'], period=20, std_dev=2
            )
            self.indicators['bollinger'] = {
                'upper': upper,
                'middle': middle,
                'lower': lower
            }
            
            # 计算移动平均线
            self.indicators['ma'] = TechnicalIndicators.calculate_moving_averages(
                self.data['Close'], periods=[5, 10, 20]
            )
            
            # 计算MACD
            self.indicators['macd'] = TechnicalIndicators.calculate_macd(
                self.data['Close'], fast_period=12, slow_period=26, signal_period=9
            )
            
            # 计算成交量指标
            self.indicators['volume'] = TechnicalIndicators.calculate_volume_indicators(
                self.data['Volume'], self.data['Close'], period=20
            )
            
            # 计算筹码分布
            print("正在计算筹码分布...")
            self.indicators['chip_distribution'] = TechnicalIndicators.calculate_chip_distribution(
                self.data['Close'], self.data['Volume']
            )
            
            # 计算市盈率分析
            print("正在获取市盈率数据...")
            self.indicators['pe_analysis'] = TechnicalIndicators.calculate_pe_analysis(
                self.stock_code
            )
            
            # 计算基本面指标
            print("正在获取基本面指标...")
            self.indicators['fundamental'] = TechnicalIndicators.calculate_fundamental_indicators(
                self.stock_code
            )
            
            print("技术指标计算完成")
            return True
            
        except Exception as e:
            print(f"计算技术指标失败: {e}")
            return False
    
    def generate_signals(self):
        """生成交易信号（实现抽象方法）"""
        return self.generate_trading_signals()
    
    def generate_trading_signals(self):
        """生成交易信号"""
        if not self.indicators:
            print("请先计算技术指标")
            return None
        
        try:
            print("正在生成交易信号...")
            
            # 创建信号生成器
            self.signal_generator = SignalGenerator(self.data, self.indicators)
            
            # 生成综合信号
            self.signals = self.signal_generator.generate_comprehensive_signals()
            
            # 添加基本面分析
            print("正在获取基本面分析...")
            try:
                # 获取市盈率分析
                pe_analysis = TechnicalIndicators.calculate_pe_analysis(self.stock_code)
                self.signals['pe_analysis'] = pe_analysis
                
                # 获取基本面指标
                fundamental_indicators = TechnicalIndicators.calculate_fundamental_indicators(self.stock_code)
                self.signals['fundamental_indicators'] = fundamental_indicators
                
                print("基本面分析获取完成")
            except Exception as e:
                print(f"基本面分析获取失败: {e}")
                self.signals['pe_analysis'] = None
                self.signals['fundamental_indicators'] = {}
            
            print("交易信号生成完成")
            return self.signals
            
        except Exception as e:
            print(f"生成交易信号失败: {e}")
            return None
    
    def generate_chart(self, chart_type: str = "comprehensive", save_path: Optional[str] = None):
        """
        生成图表
        :param chart_type: 图表类型 (comprehensive, candlestick, volume, macd, rsi, chip)
        :param save_path: 保存路径
        :return: Plotly图表对象
        """
        if not self.indicators:
            print("请先计算技术指标")
            return None
        
        try:
            # 创建图表生成器
            self.chart_generator = ChartGenerator(self.data, self.indicators)
            
            # 根据类型生成图表
            if chart_type == "comprehensive":
                fig = self.chart_generator.create_comprehensive_chart(
                    f"{self.stock_name}({self.stock_code}) 综合分析图"
                )
            elif chart_type == "candlestick":
                fig = self.chart_generator.create_candlestick_chart(
                    f"{self.stock_name}({self.stock_code}) K线图"
                )
            elif chart_type == "volume":
                fig = self.chart_generator.create_volume_chart(
                    f"{self.stock_name}({self.stock_code}) 成交量图"
                )
            elif chart_type == "macd":
                fig = self.chart_generator.create_macd_chart(
                    f"{self.stock_name}({self.stock_code}) MACD指标图"
                )
            elif chart_type == "rsi":
                fig = self.chart_generator.create_rsi_chart(
                    f"{self.stock_name}({self.stock_code}) RSI指标图"
                )
            elif chart_type == "chip":
                fig = self.chart_generator.create_chip_distribution_chart(
                    f"{self.stock_name}({self.stock_code}) 筹码分布图"
                )
            else:
                print(f"不支持的图表类型: {chart_type}")
                return None
            
            # 保存图表
            if save_path:
                fig.write_html(save_path)
                print(f"图表已保存到: {save_path}")
            
            return fig
            
        except Exception as e:
            print(f"生成图表失败: {e}")
            return None
    
    def get_latest_analysis(self):
        """获取最新分析结果"""
        if not self.signals:
            return None
        
        return {
            'stock_info': {
                'code': self.stock_code,
                'name': self.stock_name
            },
            'latest_price': {
                'close': self.data['Close'].iloc[-1],
                'change': self.data['Close'].iloc[-1] - self.data['Close'].iloc[-2] if len(self.data) > 1 else 0,
                'change_pct': ((self.data['Close'].iloc[-1] / self.data['Close'].iloc[-2] - 1) * 100) if len(self.data) > 1 else 0
            },
            'signals': self.signals,
            'indicators': {
                'rsi': self.indicators.get('rsi', pd.Series()).iloc[-1] if 'rsi' in self.indicators else None,
                'macd': self.indicators.get('macd', {}).get('macd', pd.Series()).iloc[-1] if 'macd' in self.indicators else None,
                'ma20': self.indicators.get('ma', {}).get(20, pd.Series()).iloc[-1] if 'ma' in self.indicators and 20 in self.indicators['ma'] else None
            }
        }
    
    def print_analysis_summary(self):
        """打印分析摘要"""
        if not self.signals:
            print("请先生成交易信号")
            return
        
        print("\n" + "="*60)
        print(f"📊 {self.stock_name}({self.stock_code}) 分析摘要")
        print("="*60)
        
        # 基本信息
        latest_close = self.data['Close'].iloc[-1]
        print(f"当前价格: {latest_close:.2f}")
        
        if len(self.data) > 1:
            change = latest_close - self.data['Close'].iloc[-2]
            change_pct = (change / self.data['Close'].iloc[-2]) * 100
            print(f"涨跌幅: {change:+.2f} ({change_pct:+.2f}%)")
        
        # 主要信号
        print(f"\n🎯 主要信号: {self.signals['signal_type']}")
        print(f"信号强度: {self.signals['signal_strength']}")
        
        # 买入信号
        if self.signals['buy_signals']:
            print(f"\n🟢 买入信号 ({len(self.signals['buy_signals'])}个):")
            for signal in self.signals['buy_signals'][:5]:  # 最多显示5个
                print(f"  • {signal}")
        
        # 卖出信号
        if self.signals['sell_signals']:
            print(f"\n🔴 卖出信号 ({len(self.signals['sell_signals'])}个):")
            for signal in self.signals['sell_signals'][:5]:  # 最多显示5个
                print(f"  • {signal}")
        
        # 技术指标
        print(f"\n📈 技术指标:")
        if 'rsi' in self.indicators:
            rsi_value = self.indicators['rsi'].iloc[-1]
            print(f"  RSI: {rsi_value:.2f}")
        
        if 'macd' in self.indicators:
            macd_value = self.indicators['macd']['macd'].iloc[-1]
            print(f"  MACD: {macd_value:.4f}")
        
        if 'ma' in self.indicators and 20 in self.indicators['ma']:
            ma20_value = self.indicators['ma'][20].iloc[-1]
            print(f"  MA20: {ma20_value:.2f}")
        
        print("="*60)
    
    def save_analysis_report(self, file_path: str):
        """保存分析报告"""
        if not self.signals:
            print("请先生成交易信号")
            return False
        
        try:
            report = {
                'stock_info': {
                    'code': self.stock_code,
                    'name': self.stock_name,
                    'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'data_info': {
                    'period': self.time_period,
                    'data_points': len(self.data),
                    'date_range': f"{self.data['Date'].min()} 到 {self.data['Date'].max()}"
                },
                'signals': self.signals,
                'indicators_summary': {
                    'rsi': self.indicators.get('rsi', pd.Series()).iloc[-1] if 'rsi' in self.indicators else None,
                    'macd': self.indicators.get('macd', {}).get('macd', pd.Series()).iloc[-1] if 'macd' in self.indicators else None,
                    'ma20': self.indicators.get('ma', {}).get(20, pd.Series()).iloc[-1] if 'ma' in self.indicators and 20 in self.indicators['ma'] else None
                }
            }
            
            # 保存为JSON文件
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"分析报告已保存到: {file_path}")
            return True
            
        except Exception as e:
            print(f"保存分析报告失败: {e}")
            return False
    
    def fetch_data(self, start_date: str, end_date: str, time_period: str = "daily") -> bool:
        """获取股票数据"""
        try:
            print(f"正在获取 {self.stock_code} 的数据...")
            
            # 创建数据获取器
            self.data_fetcher = DataFetcher()
            
            # 获取股票数据
            self.data, self.data_source = self.data_fetcher.fetch_stock_data(
                self.stock_code, start_date, end_date, time_period
            )
            
            if self.data is None or len(self.data) == 0:
                print(f"无法获取 {self.stock_code} 的数据")
                return False
            
            # 获取股票名称
            self.stock_name = self.data_fetcher.get_stock_name(self.stock_code)
            print(f"股票名称: {self.stock_name}")
            
            print(f"数据获取成功: {len(self.data)} 条记录，数据源: {self.data_source}")
            return True
            
        except Exception as e:
            print(f"获取数据失败: {e}")
            return False 