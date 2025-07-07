"""
多数据源股票数据获取器
支持akshare和tushare，优先使用akshare，不支持的部分用tushare作为备用
"""

import pandas as pd
import numpy as np
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')

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

class DataFetcher:
    """多数据源数据获取器"""
    
    def __init__(self):
        """初始化数据获取器"""
        self.akshare_available = self._check_akshare()
        self.tushare_available = self._check_tushare()
        
        print(f"数据源状态: akshare={self.akshare_available}, tushare={self.tushare_available}")
    
    def _check_akshare(self) -> bool:
        """检查akshare是否可用"""
        try:
            import akshare as ak
            # 简单测试akshare
            test_data = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20240101", end_date="20240102")
            return test_data is not None and len(test_data) > 0
        except Exception as e:
            print(f"akshare检查失败: {e}")
            return False
    
    def _check_tushare(self) -> bool:
        """检查tushare是否可用"""
        try:
            import tushare as ts
            token = get_tushare_token()
            if not token:
                print("tushare token未配置，跳过tushare检查")
                return False
            ts.set_token(token)
            pro = ts.pro_api()
            # 简单测试tushare
            test_data = pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20240102')
            return test_data is not None and len(test_data) > 0
        except Exception as e:
            print(f"tushare检查失败: {e}")
            return False
    
    def fetch_stock_data(self, stock_code: str, start_date: str, end_date: str, 
                        time_period: str = "daily") -> Tuple[Optional[pd.DataFrame], str]:
        """
        获取股票数据
        :param stock_code: 股票代码
        :param start_date: 开始日期 (YYYYMMDD)
        :param end_date: 结束日期 (YYYYMMDD)
        :param time_period: 时间周期 (daily, 60, 30, 15)
        :return: (数据DataFrame, 数据源名称)
        """
        print(f"正在获取 {stock_code} 的{self._get_period_name(time_period)}数据...")
        
        # 尝试akshare
        if self.akshare_available:
            data, source = self._fetch_from_akshare(stock_code, start_date, end_date, time_period)
            if data is not None and len(data) > 0:
                return data, source
        
        # akshare失败，尝试tushare
        if self.tushare_available:
            data, source = self._fetch_from_tushare(stock_code, start_date, end_date, time_period)
            if data is not None and len(data) > 0:
                return data, source
        
        print(f"所有数据源都无法获取 {stock_code} 的数据")
        return None, "none"
    
    def _fetch_from_akshare(self, stock_code: str, start_date: str, end_date: str, 
                           time_period: str) -> Tuple[Optional[pd.DataFrame], str]:
        """从akshare获取数据"""
        try:
            import akshare as ak
            
            if time_period == "weekly":
                # 周线数据
                data = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="weekly",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"
                )
                source = "akshare_weekly"
            elif time_period == "daily":
                # 日线数据
                data = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"
                )
                source = "akshare_daily"
            else:
                # 尝试获取分钟线数据
                try:
                    period_map = {"60": "60", "30": "30", "15": "15"}
                    period = period_map.get(time_period, "60")
                    
                    # 尝试不同的分钟线接口
                    try:
                        # 方法1: stock_zh_a_minute
                        data = ak.stock_zh_a_minute(
                            symbol=stock_code,
                            period=period,
                            start_date=start_date,
                            end_date=end_date,
                            adjust="qfq"
                        )
                        source = f"akshare_{period}min"
                    except:
                        # 方法2: stock_zh_a_hist_min_em
                        data = ak.stock_zh_a_hist_min_em(
                            symbol=stock_code,
                            period=period,
                            start_date=start_date,
                            end_date=end_date,
                            adjust="qfq"
                        )
                        source = f"akshare_{period}min_em"
                        
                except Exception as e:
                    print(f"akshare分钟线获取失败: {e}")
                    # 回退到日线数据
                    data = ak.stock_zh_a_hist(
                        symbol=stock_code,
                        period="daily",
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq"
                    )
                    source = "akshare_daily_fallback"
            
            if data is not None and len(data) > 0:
                # 标准化列名
                data = self._standardize_akshare_columns(data, time_period)
                print(f"akshare获取成功: {len(data)} 条记录")
                return data, source
            else:
                print("akshare返回空数据")
                return None, "akshare_empty"
                
        except Exception as e:
            print(f"akshare获取失败: {e}")
            return None, "akshare_error"
    
    def _fetch_from_tushare(self, stock_code: str, start_date: str, end_date: str, 
                           time_period: str) -> Tuple[Optional[pd.DataFrame], str]:
        """从tushare获取数据"""
        try:
            import tushare as ts
            
            token = get_tushare_token()
            if not token:
                print("tushare token未配置，无法获取数据")
                return None, "tushare_no_token"
            
            ts.set_token(token)
            pro = ts.pro_api()
            
            # 转换股票代码格式
            ts_code = self._convert_to_tushare_code(stock_code)
            
            if time_period == "weekly":
                # 周线数据
                data = pro.weekly(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )
                source = "tushare_weekly"
            elif time_period == "daily":
                # 日线数据
                data = pro.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )
                source = "tushare_daily"
            else:
                # tushare的分钟线数据需要特殊处理
                # 暂时使用日线数据
                data = pro.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )
                source = "tushare_daily_fallback"
            
            if data is not None and len(data) > 0:
                # 标准化列名
                data = self._standardize_tushare_columns(data, time_period)
                print(f"tushare获取成功: {len(data)} 条记录")
                return data, source
            else:
                print("tushare返回空数据")
                return None, "tushare_empty"
                
        except Exception as e:
            print(f"tushare获取失败: {e}")
            return None, "tushare_error"
    
    def _convert_to_tushare_code(self, stock_code: str) -> str:
        """转换股票代码为tushare格式"""
        if stock_code.startswith('6'):
            return f"{stock_code}.SH"
        else:
            return f"{stock_code}.SZ"
    
    def _standardize_akshare_columns(self, data: pd.DataFrame, time_period: str) -> pd.DataFrame:
        """标准化akshare数据列名"""
        if time_period == "weekly":
            # 周线数据列名映射
            cols_mapping = {
                '日期': 'Date',
                '开盘': 'Open', 
                '收盘': 'Close',
                '最高': 'High',
                '最低': 'Low',
                '成交量': 'Volume',
                '成交额': 'Amount',
                '振幅': 'Amplitude',
                '涨跌幅': 'Pct_chg',
                '涨跌额': 'Change',
                '换手率': 'Turnover'
            }
        elif time_period == "daily":
            cols_mapping = {
                '日期': 'Date',
                '开盘': 'Open', 
                '收盘': 'Close',
                '最高': 'High',
                '最低': 'Low',
                '成交量': 'Volume',
                '成交额': 'Amount',
                '振幅': 'Amplitude',
                '涨跌幅': 'Pct_chg',
                '涨跌额': 'Change',
                '换手率': 'Turnover'
            }
        else:
            # 分钟线数据列名映射
            cols_mapping = {
                '时间': 'Date',
                '开盘': 'Open', 
                '收盘': 'Close',
                '最高': 'High',
                '最低': 'Low',
                '成交量': 'Volume',
                '成交额': 'Amount'
            }
        
        # 重命名列
        existing_cols = {k: v for k, v in cols_mapping.items() if k in data.columns}
        data = data.rename(columns=existing_cols)
        
        # 确保必要的列存在
        required_cols = ['Date', 'Open', 'Close', 'High', 'Low', 'Volume']
        for col in required_cols:
            if col not in data.columns:
                print(f"警告: 缺少必要列 {col}")
        
        # 数据类型转换
        numeric_cols = ['Open', 'Close', 'High', 'Low', 'Volume']
        for col in numeric_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # 处理日期列
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date'])
        
        return data
    
    def _standardize_tushare_columns(self, data: pd.DataFrame, time_period: str) -> pd.DataFrame:
        """标准化tushare数据列名"""
        # tushare的列名映射
        cols_mapping = {
            'trade_date': 'Date',
            'open': 'Open',
            'close': 'Close',
            'high': 'High',
            'low': 'Low',
            'vol': 'Volume',
            'amount': 'Amount'
        }
        
        # 重命名列
        existing_cols = {k: v for k, v in cols_mapping.items() if k in data.columns}
        data = data.rename(columns=existing_cols)
        
        # 处理日期格式
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date'], format='%Y%m%d')
        
        # 数据类型转换
        numeric_cols = ['Open', 'Close', 'High', 'Low', 'Volume']
        for col in numeric_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # 按日期排序
        if 'Date' in data.columns:
            data = data.sort_values('Date').reset_index(drop=True)
        
        return data
    
    def _get_period_name(self, time_period: str) -> str:
        """获取时间周期名称"""
        period_names = {
            "weekly": "周线",
            "daily": "日线",
            "60": "60分钟",
            "30": "30分钟", 
            "15": "15分钟"
        }
        return period_names.get(time_period, time_period)
    
    def get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        try:
            import akshare as ak
            stock_info = ak.stock_individual_info_em(symbol=stock_code)
            if not stock_info.empty:
                name_row = stock_info[stock_info['item'] == '股票简称']
                if not name_row.empty:
                    return name_row['value'].iloc[0]
        except Exception as e:
            print(f"获取股票名称失败: {e}")
        
        return f"股票{stock_code}" 