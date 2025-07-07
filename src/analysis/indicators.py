"""
技术指标计算模块
提供各种技术指标的计算方法
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
import os

def get_tushare_token():
    """从配置文件读取tushare token"""
    try:
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        token_file = os.path.join(project_root, 'config', 'tushare_token.txt')
        
        with open(token_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and line != 'your_tushare_token_here':
                    return line
        print("警告: 未找到有效的tushare token，请在config/tushare_token.txt中填写")
        return None
    except Exception as e:
        print(f"无法读取tushare token: {e}")
        return None

class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        计算RSI指标
        :param prices: 价格序列
        :param period: 计算周期
        :return: RSI值序列
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算布林带
        :param prices: 价格序列
        :param period: 计算周期
        :param std_dev: 标准差倍数
        :return: (上轨, 中轨, 下轨)
        """
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    @staticmethod
    def calculate_moving_averages(prices: pd.Series, periods: List[int] = [5, 10, 20]) -> Dict[int, pd.Series]:
        """
        计算移动平均线
        :param prices: 价格序列
        :param periods: 计算周期列表
        :return: 各周期移动平均线字典
        """
        ma_dict = {}
        for period in periods:
            ma_dict[period] = prices.rolling(window=period).mean()
        return ma_dict
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, pd.Series]:
        """
        计算MACD指标
        :param prices: 价格序列
        :param fast_period: 快线周期
        :param slow_period: 慢线周期
        :param signal_period: 信号线周期
        :return: MACD指标字典
        """
        ema_fast = prices.ewm(span=fast_period).mean()
        ema_slow = prices.ewm(span=slow_period).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                           k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        计算随机指标
        :param high: 最高价序列
        :param low: 最低价序列
        :param close: 收盘价序列
        :param k_period: K值周期
        :param d_period: D值周期
        :return: (K值, D值)
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        return k_percent, d_percent
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        计算平均真实波幅(ATR)
        :param high: 最高价序列
        :low: 最低价序列
        :close: 收盘价序列
        :period: 计算周期
        :return: ATR值序列
        """
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def calculate_volume_indicators(volume: pd.Series, close: pd.Series, period: int = 20) -> Dict[str, pd.Series]:
        """
        计算成交量指标
        :param volume: 成交量序列
        :param close: 收盘价序列
        :param period: 计算周期
        :return: 成交量指标字典
        """
        # 成交量移动平均
        volume_ma = volume.rolling(window=period).mean()
        
        # 量比
        volume_ratio = volume / volume_ma
        
        # 价量关系
        price_change = close.pct_change()
        volume_change = volume.pct_change()
        
        # 价量配合度
        price_volume_correlation = pd.Series(index=close.index)
        for i in range(period, len(close)):
            price_volume_correlation.iloc[i] = np.corrcoef(
                price_change.iloc[i-period:i], 
                volume_change.iloc[i-period:i]
            )[0, 1]
        
        return {
            'volume_ma': volume_ma,
            'volume_ratio': volume_ratio,
            'price_volume_correlation': price_volume_correlation
        }
    
    @staticmethod
    def calculate_chip_distribution(close: pd.Series, volume: pd.Series, 
                                  price_range: int = 100) -> Dict[str, float]:
        """
        计算筹码分布
        :param close: 收盘价序列
        :param volume: 成交量序列
        :param price_range: 价格区间数量
        :return: 筹码分布信息
        """
        if len(close) < 20:
            return {
                'main_peak_price': close.iloc[-1],
                'avg_price': close.mean(),
                'pressure_level': close.max(),
                'support_level': close.min(),
                'concentration': 0.5
            }
        
        # 计算价格区间
        min_price = close.min()
        max_price = close.max()
        price_step = (max_price - min_price) / price_range
        
        # 初始化筹码分布数组
        chip_distribution = np.zeros(price_range)
        
        # 计算每个交易日的筹码分布
        for i in range(len(close)):
            price = close.iloc[i]
            vol = volume.iloc[i]
            
            # 将成交量分配到价格区间
            price_index = int((price - min_price) / price_step)
            price_index = max(0, min(price_index, price_range - 1))
            chip_distribution[price_index] += vol
        
        # 找到主要筹码峰
        main_peak_index = np.argmax(chip_distribution)
        main_peak_price = min_price + main_peak_index * price_step
        
        # 计算加权平均价格
        price_levels = np.arange(price_range) * price_step + min_price
        weighted_avg_price = np.sum(price_levels * chip_distribution) / np.sum(chip_distribution)
        
        # 计算筹码集中度
        total_chips = np.sum(chip_distribution)
        if total_chips > 0:
            concentration = np.max(chip_distribution) / total_chips
        else:
            concentration = 0
        
        # 找到压力位和支撑位
        sorted_indices = np.argsort(chip_distribution)[::-1]
        top_10_percent = sorted_indices[:int(price_range * 0.1)]
        pressure_level = min_price + np.max(top_10_percent) * price_step
        support_level = min_price + np.min(top_10_percent) * price_step
        
        return {
            'main_peak_price': main_peak_price,
            'avg_price': weighted_avg_price,
            'pressure_level': pressure_level,
            'support_level': support_level,
            'concentration': concentration,
            'distribution': chip_distribution,
            'price_levels': price_levels
        }
    
    @staticmethod
    def calculate_pe_analysis(stock_code: str) -> Dict[str, any]:
        """
        计算市盈率分析，优先用tushare，获取不到再用akshare
        :param stock_code: 股票代码
        :return: 市盈率分析信息
        """
        # 1. tushare优先
        try:
            import tushare as ts
            token = get_tushare_token()
            if token:
                ts.set_token(token)
                pro = ts.pro_api()
                # tushare股票代码格式
                if stock_code.startswith('6'):
                    ts_code = f"{stock_code}.SH"
                else:
                    ts_code = f"{stock_code}.SZ"
                df = pro.daily_basic(ts_code=ts_code, fields='ts_code,trade_date,pe,pb,ps,roe')
                if df is not None and len(df) > 0:
                    latest = df.sort_values('trade_date').iloc[-1]
                    pe = latest.get('pe', None)
                    pb = latest.get('pb', None)
                    ps = latest.get('ps', None)
                    roe = latest.get('roe', None)
                    pe_analysis = {
                        'current_pe': pe,
                        'pe_data': {'pe': pe, 'pb': pb, 'ps': ps, 'roe': roe},
                        'industry_pe': None,
                        'analysis': []
                    }
                    if pe is not None:
                        if pe < 0:
                            pe_analysis['analysis'].append("市盈率为负，公司亏损")
                        elif pe < 10:
                            pe_analysis['analysis'].append("市盈率较低，可能被低估")
                        elif pe < 20:
                            pe_analysis['analysis'].append("市盈率适中，估值合理")
                        elif pe < 30:
                            pe_analysis['analysis'].append("市盈率偏高，注意风险")
                        else:
                            pe_analysis['analysis'].append("市盈率过高，存在泡沫风险")
                        pe_analysis['analysis'].append(f"当前市盈率: {pe:.2f}")
                    return pe_analysis
        except Exception as e:
            print(f"tushare市盈率获取失败: {e}")
        
        # 2. akshare兜底 - 尝试多个接口
        try:
            import akshare as ak
            
            # 方法1: stock_financial_analysis_indicator (财务分析指标)
            try:
                df_finance = ak.stock_financial_analysis_indicator(symbol=stock_code)
                if df_finance is not None and len(df_finance) > 0:
                    # 获取最新数据
                    if '日期' in df_finance.columns:
                        latest_date = df_finance['日期'].max()
                        latest_data = df_finance[df_finance['日期'] == latest_date].iloc[0]
                        
                        # 计算市盈率 (股价/每股收益)
                        # 需要获取当前股价和每股收益
                        try:
                            # 获取当前股价
                            stock_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="qfq")
                            if not stock_data.empty:
                                current_price = stock_data.iloc[-1]['收盘']
                                
                                # 获取每股收益
                                eps = latest_data.get('摊薄每股收益(元)', None)
                                if eps is not None and eps > 0:
                                    pe = current_price / eps
                                    
                                    pe_analysis = {
                                        'current_pe': pe,
                                        'pe_data': {
                                            'pe': pe,
                                            'eps': eps,
                                            'current_price': current_price,
                                            'roe': latest_data.get('净资产收益率(%)', None),
                                            'pb': latest_data.get('每股净资产_调整前(元)', None)
                                        },
                                        'industry_pe': None,
                                        'analysis': []
                                    }
                                    
                                    if pe < 0:
                                        pe_analysis['analysis'].append("市盈率为负，公司亏损")
                                    elif pe < 10:
                                        pe_analysis['analysis'].append("市盈率较低，可能被低估")
                                    elif pe < 20:
                                        pe_analysis['analysis'].append("市盈率适中，估值合理")
                                    elif pe < 30:
                                        pe_analysis['analysis'].append("市盈率偏高，注意风险")
                                    else:
                                        pe_analysis['analysis'].append("市盈率过高，存在泡沫风险")
                                    pe_analysis['analysis'].append(f"当前市盈率: {pe:.2f}")
                                    pe_analysis['analysis'].append(f"每股收益: {eps:.4f}元")
                                    pe_analysis['analysis'].append(f"当前股价: {current_price:.2f}元")
                                    
                                    return pe_analysis
                        except Exception as e:
                            print(f"计算市盈率失败: {e}")
            except Exception as e:
                print(f"akshare stock_financial_analysis_indicator获取失败: {e}")
            
            # 方法2: stock_individual_info_em (个股信息)
            try:
                stock_info = ak.stock_individual_info_em(symbol=stock_code)
                if not stock_info.empty:
                    # 查找市盈率相关指标
                    pe_rows = stock_info[stock_info['item'].str.contains('市盈率', na=False)]
                    if not pe_rows.empty:
                        for _, row in pe_rows.iterrows():
                            value = row['value']
                            if isinstance(value, str):
                                value_clean = value.replace('倍', '').replace(',', '').strip()
                                try:
                                    pe_value = float(value_clean)
                                    pe_analysis = {
                                        'current_pe': pe_value,
                                        'pe_data': {'pe': pe_value},
                                        'industry_pe': None,
                                        'analysis': []
                                    }
                                    if pe_value < 0:
                                        pe_analysis['analysis'].append("市盈率为负，公司亏损")
                                    elif pe_value < 10:
                                        pe_analysis['analysis'].append("市盈率较低，可能被低估")
                                    elif pe_value < 20:
                                        pe_analysis['analysis'].append("市盈率适中，估值合理")
                                    elif pe_value < 30:
                                        pe_analysis['analysis'].append("市盈率偏高，注意风险")
                                    else:
                                        pe_analysis['analysis'].append("市盈率过高，存在泡沫风险")
                                    pe_analysis['analysis'].append(f"当前市盈率: {pe_value:.2f}")
                                    return pe_analysis
                                except ValueError:
                                    continue
            except Exception as e:
                print(f"akshare stock_individual_info_em获取失败: {e}")
                
        except Exception as e:
            print(f"akshare市盈率获取失败: {e}")
        
        return {
            'current_pe': None,
            'pe_data': {},
            'industry_pe': None,
            'analysis': ["无法获取市盈率数据"]
        }

    @staticmethod
    def calculate_fundamental_indicators(stock_code: str) -> Dict[str, any]:
        """
        计算基本面指标，优先用tushare，获取不到再用akshare
        :param stock_code: 股票代码
        :return: 基本面指标信息
        """
        # 1. AkShare 免费接口优先
        try:
            import akshare as ak
            # 使用新浪财经接口，免费且无需 token
            stock_info = ak.stock_individual_info_em(symbol=stock_code)
            if stock_info is not None and not stock_info.empty:
                key_indicators = ['市盈率', '市净率', '市销率', '净资产收益率', '毛利率']
                result = {}
                for indicator in key_indicators:
                    rows = stock_info[stock_info['item'].str.contains(indicator, na=False)]
                    if not rows.empty:
                        val_raw = rows.iloc[0]['value']
                        # 数据清洗：去掉百分号/倍/逗号等非数字字符
                        if isinstance(val_raw, str):
                            clean = val_raw.replace('%', '').replace('倍', '').replace(',', '').strip()
                            try:
                                val_num = float(clean)
                            except ValueError:
                                val_num = None
                        else:
                            val_num = val_raw
                        if val_num is not None and not pd.isna(val_num):
                            result[indicator] = val_num
                if result:
                    return result
        except Exception as e:
            print(f"akshare基本面获取失败: {e}")

        # 2. tushare 备用（部分接口收费，可能无权限）
        try:
            import tushare as ts
            token = get_tushare_token()
            if token:
                ts.set_token(token)
                pro = ts.pro_api()
                if stock_code.startswith('6'):
                    ts_code = f"{stock_code}.SH"
                else:
                    ts_code = f"{stock_code}.SZ"
                df = pro.daily_basic(ts_code=ts_code, fields='ts_code,trade_date,pe,pb,ps,roe')
                if df is not None and len(df) > 0:
                    latest = df.sort_values('trade_date').iloc[-1]
                    result = {
                        '市盈率': latest.get('pe', None),
                        '市净率': latest.get('pb', None),
                        '市销率': latest.get('ps', None),
                        '净资产收益率': latest.get('roe', None)
                    }
                    result = {k: v for k, v in result.items() if v is not None and not pd.isna(v)}
                    if result:
                        return result
        except Exception as e:
            print(f"tushare基本面获取失败: {e}")
        
        return {} 