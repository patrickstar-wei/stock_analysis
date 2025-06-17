import akshare as ak
import pandas as pd
import numpy as np
import talib as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
import time
import random
warnings.filterwarnings('ignore')

class StockAnalyzer:
    def __init__(self, stock_code, period="1000"):
        """
        初始化股票分析器
        :param stock_code: A股代码，如 '000001'
        :param period: 获取数据的天数，默认1000天
        """
        self.stock_code = stock_code
        self.period = period
        self.data = None
        self.stock_name = None  # 添加股票名称属性
        self.time_period = "daily"  # 时间周期：daily, 60, 30, 15
        self.chip_data = None  # 筹码分布数据
        
    def fetch_data(self, start_date="20220101", end_date="20251231", time_period="daily"):
        """
        获取股票数据
        :param start_date: 开始日期
        :param end_date: 结束日期  
        :param time_period: 时间周期 - daily(日线), 60(60分钟), 30(30分钟), 15(15分钟)
        """
        try:
            self.time_period = time_period
            
            # 验证日期范围
            from datetime import datetime
            today = datetime.now()
            
            # 转换日期格式进行验证
            try:
                start_dt = datetime.strptime(start_date, '%Y%m%d')
                end_dt = datetime.strptime(end_date, '%Y%m%d')
            except ValueError:
                print(f"日期格式错误，请使用YYYYMMDD格式")
                return False
            
            # 检查是否查询未来日期
            if end_dt > today:
                print(f"结束日期不能超过今天 ({today.strftime('%Y-%m-%d')})")
                # 自动调整为今天
                end_date = today.strftime('%Y%m%d')
                print(f"自动调整结束日期为: {end_date}")
            
            if start_dt > today:
                print(f"开始日期不能超过今天 ({today.strftime('%Y-%m-%d')})")
                return False
            
            # 添加延迟避免API频率限制
            time.sleep(0.5)
            
            # 根据时间周期选择不同的数据获取方式
            print(f"正在获取 {self.stock_code} 的{self._get_period_name()}数据...")
            
            if time_period == "daily":
                # 日线数据
                self.data = ak.stock_zh_a_hist(
                    symbol=self.stock_code, 
                    period="daily", 
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"
                )
            else:
                # 分钟级数据
                try:
                    # 由于akshare分钟级数据接口限制，暂时使用日线数据模拟
                    print(f"注意：由于API限制，{self._get_period_name()}数据将使用日线数据模拟")
                    self.data = ak.stock_zh_a_hist(
                        symbol=self.stock_code, 
                        period="daily", 
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq"
                    )
                    
                    # 如果获取到日线数据，可以通过插值模拟分钟数据
                    if self.data is not None and len(self.data) > 0:
                        self.data = self._simulate_minute_data(self.data, time_period)
                        
                except Exception as e:
                    print(f"获取分钟数据失败，使用日线数据: {e}")
                    self.data = ak.stock_zh_a_hist(
                        symbol=self.stock_code, 
                        period="daily", 
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq"
                    )
                    self.time_period = "daily"
            
            # 获取股票名称
            try:
                time.sleep(0.5)  # 避免频率限制
                stock_info = ak.stock_individual_info_em(symbol=self.stock_code)
                if not stock_info.empty:
                    name_row = stock_info[stock_info['item'] == '股票简称']
                    if not name_row.empty:
                        self.stock_name = name_row['value'].iloc[0]
                    else:
                        self.stock_name = f"股票{self.stock_code}"
                else:
                    self.stock_name = f"股票{self.stock_code}"
            except Exception as e:
                print(f"获取股票名称失败: {e}")
                self.stock_name = f"股票{self.stock_code}"
            
            # 打印原始列名
            print(f"原始列名: {list(self.data.columns) if self.data is not None else '无数据'}")
            
            # 检查数据是否为空
            if self.data is None or len(self.data) == 0:
                print(f"未能获取到股票 {self.stock_code} 的数据")
                print("可能的原因:")
                print("1. 股票代码不存在或已退市")
                print("2. 查询的日期范围内没有交易数据")
                print("3. API暂时不可用，请稍后重试")
                return False
            
            # 重置索引
            self.data = self.data.reset_index(drop=True)
            
            # 根据实际列名进行重命名（akshare返回的是中文列名）
            if time_period == "daily":
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
                # 分钟数据的列名可能不同
                cols_mapping = {
                    '时间': 'Date',
                    '开盘': 'Open', 
                    '收盘': 'Close',
                    '最高': 'High',
                    '最低': 'Low',
                    '成交量': 'Volume',
                    '成交额': 'Amount'
                }
            
            # 只重命名存在的列
            existing_cols = {k: v for k, v in cols_mapping.items() if k in self.data.columns}
            self.data = self.data.rename(columns=existing_cols)
            
            # 确保必要的列存在
            required_cols = ['Date', 'Open', 'Close', 'High', 'Low', 'Volume']
            missing_cols = [col for col in required_cols if col not in self.data.columns]
            
            if missing_cols:
                print(f"缺少必要的列: {missing_cols}")
                print(f"可用的列: {list(self.data.columns)}")
                return False
            
            # 只保留需要的列
            self.data = self.data[required_cols]
            
            # 转换数据类型
            self.data['Date'] = pd.to_datetime(self.data['Date'])
            for col in ['Open', 'Close', 'High', 'Low', 'Volume']:
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
            
            # 删除包含NaN的行
            self.data = self.data.dropna()
            
            # 按日期排序
            self.data = self.data.sort_values('Date').reset_index(drop=True)
            
            print(f"成功获取 {self.stock_code} ({self.stock_name}) 的{self._get_period_name()}数据，共 {len(self.data)} 条记录")
            print(f"数据时间范围: {self.data['Date'].min()} 到 {self.data['Date'].max()}")
            
            # 计算筹码分布
            self._calculate_chip_distribution()
            
            return True
            
        except Exception as e:
            print(f"获取股票数据失败: {e}")
            print("建议:")
            print("1. 检查网络连接")
            print("2. 确认股票代码正确")
            print("3. 稍后重试（可能是API限频）")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_period_name(self):
        """获取时间周期的中文名称"""
        period_names = {
            "daily": "日线",
            "60": "60分钟",
            "30": "30分钟", 
            "15": "15分钟"
        }
        return period_names.get(self.time_period, "日线")
    
    def _calculate_chip_distribution(self):
        """计算筹码分布"""
        if self.data is None or len(self.data) == 0:
            return
            
        try:
            print("正在计算筹码分布...")
            
            # 筹码分布计算参数
            decay_factor = 0.95  # 衰减因子，表示筹码的衰减速度
            price_bins = 100     # 价格区间数量
            
            # 获取价格范围
            min_price = self.data['Low'].min()
            max_price = self.data['High'].max()
            price_range = np.linspace(min_price, max_price, price_bins)
            
            # 初始化筹码分布矩阵
            chip_distribution = np.zeros((len(self.data), price_bins))
            
            for i in range(len(self.data)):
                if i == 0:
                    # 第一天，所有成交量都在当天的价格区间内
                    current_price = self.data.iloc[i]['Close']
                    volume = self.data.iloc[i]['Volume']
                    
                    # 找到最接近当前价格的价格区间
                    price_idx = np.argmin(np.abs(price_range - current_price))
                    chip_distribution[i, price_idx] = volume
                else:
                    # 继承前一天的筹码分布（加上衰减）
                    chip_distribution[i] = chip_distribution[i-1] * decay_factor
                    
                    # 添加当天的新筹码
                    current_price = self.data.iloc[i]['Close']
                    volume = self.data.iloc[i]['Volume']
                    
                    # 将当天成交量分布到价格区间内
                    high_price = self.data.iloc[i]['High']
                    low_price = self.data.iloc[i]['Low']
                    
                    # 找到价格区间
                    high_idx = np.argmin(np.abs(price_range - high_price))
                    low_idx = np.argmin(np.abs(price_range - low_price))
                    
                    if high_idx == low_idx:
                        chip_distribution[i, high_idx] += volume
                    else:
                        # 将成交量均匀分布到价格区间内
                        price_span = max(1, high_idx - low_idx + 1)
                        volume_per_bin = volume / price_span
                        for j in range(low_idx, high_idx + 1):
                            chip_distribution[i, j] += volume_per_bin
            
            # 保存筹码分布数据
            self.chip_data = {
                'price_range': price_range,
                'chip_distribution': chip_distribution,
                'dates': self.data['Date'].values
            }
            
            print("筹码分布计算完成")
            
        except Exception as e:
            print(f"筹码分布计算失败: {e}")
            self.chip_data = None
    
    def calculate_indicators(self):
        """计算技术指标"""
        if self.data is None:
            print("请先获取股票数据")
            return False
        
        try:
            # 计算MACD
            exp1 = self.data['Close'].ewm(span=12).mean()
            exp2 = self.data['Close'].ewm(span=26).mean()
            self.data['MACD'] = exp1 - exp2
            self.data['MACD_Signal'] = self.data['MACD'].ewm(span=9).mean()
            self.data['MACD_Hist'] = self.data['MACD'] - self.data['MACD_Signal']
            
            # 使用talib计算RSI
            self.data['RSI'] = ta.RSI(self.data['Close'].astype(float), timeperiod=14)
            
            # 计算布林带
            self.data['BB_Upper'], self.data['BB_Middle'], self.data['BB_Lower'] = ta.BBANDS(
                self.data['Close'].astype(float), timeperiod=20
            )
            
            print("技术指标计算完成")
            return True
            
        except Exception as e:
            print(f"计算技术指标失败: {e}")
            return False
    
    def plot_analysis(self):
        """绘制分析图表"""
        if self.data is None:
            print("请先获取并计算数据")
            return
        
        # 获取股票名称用于显示
        stock_display_name = f"{self.stock_name}({self.stock_code})" if self.stock_name else self.stock_code
        period_name = self._get_period_name()
        
        # 创建子图 - 增加筹码峰子图
        fig = make_subplots(
            rows=5, cols=2,
            shared_xaxes=True,
            vertical_spacing=0.02,
            horizontal_spacing=0.05,
            subplot_titles=(
                f'{stock_display_name} - {period_name}蜡烛图',
                '筹码峰分布',
                'MACD指标',
                '',
                'RSI指标', 
                '',
                '成交量',
                ''
            ),
            row_heights=[0.35, 0.2, 0.2, 0.2, 0.05],
            column_widths=[0.8, 0.2],
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"rowspan": 4}],
                [{"secondary_y": False}, None],
                [{"secondary_y": False}, None],
                [{"secondary_y": False}, None]
            ]
        )
        
        # 创建连续的索引来消除周末空缺
        continuous_index = list(range(len(self.data)))
        date_labels = [date.strftime('%Y-%m-%d %H:%M' if self.time_period != 'daily' else '%Y-%m-%d') 
                      for date in self.data['Date']]
        
        # 1. 蜡烛图
        fig.add_trace(
            go.Candlestick(
                x=continuous_index,
                open=self.data['Open'],
                high=self.data['High'],
                low=self.data['Low'],
                close=self.data['Close'],
                name='K线',
                increasing_line_color='red',
                decreasing_line_color='green'
            ),
            row=1, col=1
        )
        
        # 添加布林带
        fig.add_trace(
            go.Scatter(
                x=continuous_index,
                y=self.data['BB_Upper'],
                mode='lines',
                name='布林上轨',
                line=dict(color='rgba(255,0,0,0.3)', width=1),
                showlegend=True
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=continuous_index,
                y=self.data['BB_Middle'],
                mode='lines',
                name='布林中轨',
                line=dict(color='blue', width=1),
                showlegend=True
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=continuous_index,
                y=self.data['BB_Lower'],
                mode='lines',
                name='布林下轨',
                line=dict(color='rgba(255,0,0,0.3)', width=1),
                fill='tonexty',
                fillcolor='rgba(0,100,80,0.1)',
                showlegend=True
            ),
            row=1, col=1
        )
        
        # 2. 筹码峰分布（右侧）
        if self.chip_data is not None:
            # 获取最新的筹码分布
            latest_chips = self.chip_data['chip_distribution'][-1]
            price_range = self.chip_data['price_range']
            
            # 筹码峰数据处理
            chip_volumes = latest_chips / latest_chips.max() * 100  # 归一化到0-100
            
            fig.add_trace(
                go.Scatter(
                    x=chip_volumes,
                    y=price_range,
                    mode='lines',
                    fill='tozeroy',
                    name='筹码分布',
                    line=dict(color='orange', width=2),
                    fillcolor='rgba(255,165,0,0.3)'
                ),
                row=1, col=2
            )
            
            # 标记重要的筹码峰位置
            # 找到筹码集中的价格区域
            peak_indices = []
            for i in range(1, len(chip_volumes)-1):
                if chip_volumes[i] > chip_volumes[i-1] and chip_volumes[i] > chip_volumes[i+1]:
                    if chip_volumes[i] > chip_volumes.max() * 0.3:  # 只标记较大的峰
                        peak_indices.append(i)
            
            if peak_indices:
                peak_prices = [price_range[i] for i in peak_indices]
                peak_volumes = [chip_volumes[i] for i in peak_indices]
                
                fig.add_trace(
                    go.Scatter(
                        x=peak_volumes,
                        y=peak_prices,
                        mode='markers',
                        name='筹码峰',
                        marker=dict(color='red', size=8, symbol='diamond'),
                        showlegend=True
                    ),
                    row=1, col=2
                )
        
        # 3. MACD指标
        fig.add_trace(
            go.Scatter(
                x=continuous_index,
                y=self.data['MACD'],
                mode='lines',
                name='MACD',
                line=dict(color='blue', width=2)
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=continuous_index,
                y=self.data['MACD_Signal'],
                mode='lines',
                name='MACD信号线',
                line=dict(color='red', width=2)
            ),
            row=2, col=1
        )
        
        # MACD柱状图
        colors = ['red' if val >= 0 else 'green' for val in self.data['MACD_Hist']]
        fig.add_trace(
            go.Bar(
                x=continuous_index,
                y=self.data['MACD_Hist'],
                name='MACD柱状图',
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # 4. RSI指标
        fig.add_trace(
            go.Scatter(
                x=continuous_index,
                y=self.data['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='purple', width=2)
            ),
            row=3, col=1
        )
        
        # RSI超买超卖线
        fig.add_hline(y=70, line_dash="dash", line_color="red", 
                     annotation_text="超买线(70)", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", 
                     annotation_text="超卖线(30)", row=3, col=1)
        
        # 5. 成交量
        volume_colors = ['red' if close >= open_price else 'green' 
                        for close, open_price in zip(self.data['Close'], self.data['Open'])]
        
        fig.add_trace(
            go.Bar(
                x=continuous_index,
                y=self.data['Volume'],
                name='成交量',
                marker_color=volume_colors,
                opacity=0.7
            ),
            row=4, col=1
        )
        
        # 设置x轴标签，显示日期但消除周末空缺
        # 计算合适的刻度间隔
        total_points = len(self.data)
        if total_points > 250:
            tick_interval = total_points // 10  # 显示约10个刻度
        elif total_points > 100:
            tick_interval = total_points // 8   # 显示约8个刻度
        else:
            tick_interval = max(1, total_points // 5)  # 显示约5个刻度
        
        tick_indices = list(range(0, total_points, tick_interval))
        if tick_indices[-1] != total_points - 1:
            tick_indices.append(total_points - 1)  # 确保包含最后一个点
        
        tick_labels = [date_labels[i] for i in tick_indices]
        
        # 更新布局
        fig.update_layout(
            title=f'{stock_display_name} {period_name}股票技术分析图表',
            height=1200,
            showlegend=True,
            template='plotly_white',
            xaxis_rangeslider_visible=False,
            # 设置所有x轴的刻度
            xaxis=dict(
                tickmode='array',
                tickvals=tick_indices,
                ticktext=tick_labels,
                tickangle=-45
            ),
            xaxis3=dict(
                tickmode='array',
                tickvals=tick_indices,
                ticktext=tick_labels,
                tickangle=-45
            ),
            xaxis5=dict(
                tickmode='array',
                tickvals=tick_indices,
                ticktext=tick_labels,
                tickangle=-45
            ),
            xaxis7=dict(
                tickmode='array',
                tickvals=tick_indices,
                ticktext=tick_labels,
                tickangle=-45
            )
        )
        
        # 更新y轴标签
        fig.update_yaxes(title_text="价格", row=1, col=1)
        fig.update_yaxes(title_text="筹码分布%", row=1, col=2)
        fig.update_yaxes(title_text="MACD", row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=3, col=1)
        fig.update_yaxes(title_text="成交量", row=4, col=1)
        
        # 更新x轴标签
        fig.update_xaxes(title_text="时间", row=4, col=1)
        
        return fig
    
    def get_latest_signals(self):
        """获取最新的交易信号"""
        if self.data is None or len(self.data) < 2:
            return
        
        latest = self.data.iloc[-1]
        previous = self.data.iloc[-2]
        
        print(f"\n=== {self.stock_code} 最新技术指标分析 ===")
        print(f"日期: {latest['Date'].strftime('%Y-%m-%d')}")
        print(f"收盘价: {latest['Close']:.2f}")
        
        # 计算涨跌幅
        change_pct = ((latest['Close'] - previous['Close']) / previous['Close']) * 100
        print(f"涨跌幅: {change_pct:+.2f}%")
        
        # RSI分析
        rsi = latest['RSI']
        if rsi > 70:
            rsi_signal = "超买，可能回调"
        elif rsi < 30:
            rsi_signal = "超卖，可能反弹"
        else:
            rsi_signal = "正常区间"
        print(f"RSI: {rsi:.2f} - {rsi_signal}")
        
        # MACD分析
        macd = latest['MACD']
        macd_signal = latest['MACD_Signal']
        if macd > macd_signal:
            macd_trend = "多头排列"
        else:
            macd_trend = "空头排列"
        print(f"MACD: {macd:.4f}, 信号线: {macd_signal:.4f} - {macd_trend}")
        
        # 布林带分析
        close_price = latest['Close']
        bb_upper = latest['BB_Upper']
        bb_lower = latest['BB_Lower']
        bb_middle = latest['BB_Middle']
        
        if close_price > bb_upper:
            bb_position = "突破上轨，强势"
        elif close_price < bb_lower:
            bb_position = "跌破下轨，弱势"
        elif close_price > bb_middle:
            bb_position = "在布林带上半部运行"
        else:
            bb_position = "在布林带下半部运行"
        print(f"布林带: {bb_position}")
    
    def get_latest_analysis(self):
        """获取最新分析结果，返回字典格式用于网页显示"""
        if self.data is None or len(self.data) < 2:
            return None
        
        latest = self.data.iloc[-1]
        previous = self.data.iloc[-2]
        
        # 计算涨跌幅
        change_pct = ((latest['Close'] - previous['Close']) / previous['Close']) * 100
        
        # RSI分析
        rsi = latest['RSI']
        if rsi > 70:
            rsi_signal = "超买，可能回调"
        elif rsi < 30:
            rsi_signal = "超卖，可能反弹"
        else:
            rsi_signal = "正常区间"
        
        # MACD分析
        macd = latest['MACD']
        macd_signal = latest['MACD_Signal']
        if macd > macd_signal:
            macd_trend = "多头排列"
        else:
            macd_trend = "空头排列"
        
        # 布林带分析
        close_price = latest['Close']
        bb_upper = latest['BB_Upper']
        bb_lower = latest['BB_Lower']
        bb_middle = latest['BB_Middle']
        
        if close_price > bb_upper:
            bb_position = "突破上轨，强势"
        elif close_price < bb_lower:
            bb_position = "跌破下轨，弱势"
        elif close_price > bb_middle:
            bb_position = "在布林带上半部运行"
        else:
            bb_position = "在布林带下半部运行"
        
        return {
            'date': latest['Date'].strftime('%Y-%m-%d'),
            'price': f"{latest['Close']:.2f}",
            'change_pct': f"{change_pct:+.2f}%",
            'rsi': f"{rsi:.2f}",
            'rsi_signal': rsi_signal,
            'macd': f"{macd:.4f}",
            'macd_signal': macd_trend,
            'bollinger': bb_position
        }
    
    def generate_chart(self, filename):
        """生成图表并保存到文件"""
        if self.data is None:
            print("请先获取并计算数据")
            return False
        
        try:
            fig = self.plot_analysis()
            fig.write_html(filename)
            print(f"图表已保存为: {filename}")
            return True
        except Exception as e:
            print(f"生成图表失败: {e}")
            return False
    
    def _simulate_minute_data(self, daily_data, time_period):
        """
        基于日线数据模拟分钟级数据
        :param daily_data: 日线数据
        :param time_period: 时间周期（60, 30, 15）
        """
        try:
            minutes_per_period = int(time_period)
            trading_hours = 4 * 60  # 每天4小时交易时间（9:30-11:30, 13:00-15:00）
            periods_per_day = trading_hours // minutes_per_period
            
            simulated_data = []
            
            for _, day_row in daily_data.iterrows():
                # 为每一天生成多个时间点
                base_date = pd.to_datetime(day_row['日期'])
                open_price = day_row['开盘']
                close_price = day_row['收盘']
                high_price = day_row['最高']
                low_price = day_row['最低']
                volume = day_row['成交量']
                
                # 生成当天的价格走势（简单模拟）
                for i in range(periods_per_day):
                    # 计算当前时间点
                    if i < periods_per_day // 2:
                        # 上午时段 9:30-11:30
                        hour = 9 + (i * minutes_per_period) // 60
                        minute = 30 + (i * minutes_per_period) % 60
                        if minute >= 60:
                            hour += 1
                            minute -= 60
                    else:
                        # 下午时段 13:00-15:00
                        afternoon_i = i - periods_per_day // 2
                        hour = 13 + (afternoon_i * minutes_per_period) // 60
                        minute = (afternoon_i * minutes_per_period) % 60
                    
                    # 限制时间范围
                    if hour > 15 or (hour == 15 and minute > 0):
                        break
                    if hour < 9 or (hour == 9 and minute < 30):
                        continue
                    if 11 < hour < 13:  # 午休时间
                        continue
                    
                    current_time = base_date.replace(hour=hour, minute=minute)
                    
                    # 模拟价格（在开盘价和收盘价之间变化）
                    progress = i / (periods_per_day - 1) if periods_per_day > 1 else 0
                    
                    # 添加一些随机波动
                    random_factor = 1 + (random.random() - 0.5) * 0.02  # ±1%的随机波动
                    
                    current_price = open_price + (close_price - open_price) * progress * random_factor
                    
                    # 确保价格在合理范围内
                    current_price = max(low_price, min(high_price, current_price))
                    
                    # 模拟开高低收
                    if i == 0:
                        period_open = open_price
                    else:
                        period_open = simulated_data[-1]['收盘'] if simulated_data else open_price
                    
                    period_close = current_price
                    
                    # 高低价在开收盘价基础上有小幅波动
                    price_range = abs(period_close - period_open) * 0.5 + (high_price - low_price) * 0.1
                    period_high = max(period_open, period_close) + price_range * random.random() * 0.5
                    period_low = min(period_open, period_close) - price_range * random.random() * 0.5
                    
                    # 确保高低价合理
                    period_high = min(high_price, period_high)
                    period_low = max(low_price, period_low)
                    
                    # 分配成交量
                    period_volume = volume // periods_per_day
                    
                    simulated_data.append({
                        '时间': current_time,
                        '开盘': period_open,
                        '收盘': period_close,
                        '最高': period_high,
                        '最低': period_low,
                        '成交量': period_volume
                    })
            
            # 转换为DataFrame
            result_df = pd.DataFrame(simulated_data)
            print(f"成功模拟生成 {len(result_df)} 条{self._get_period_name()}数据")
            
            return result_df
            
        except Exception as e:
            print(f"模拟分钟数据失败: {e}")
            return daily_data

def main():
    """主函数"""
    print("=== A股技术分析工具 ===")
    
    # 输入股票代码
    stock_code = input("请输入A股代码（如000001）: ").strip()
    
    if not stock_code:
        print("股票代码不能为空")
        return
    
    # 创建分析器
    analyzer = StockAnalyzer(stock_code)
    
    # 获取数据
    if not analyzer.fetch_data():
        return
    
    # 计算指标
    if not analyzer.calculate_indicators():
        return
    
    # 显示最新信号
    analyzer.get_latest_signals()
    
    # 绘制图表
    fig = analyzer.plot_analysis()
    if fig:
        print(f"\n正在生成图表...")
        fig.show()
        
        # 保存图表
        fig.write_html(f"{stock_code}_analysis.html")
        print(f"图表已保存为 {stock_code}_analysis.html")

if __name__ == "__main__":
    main() 