"""
股票分析器 - 使用新的模块化架构
向后兼容的包装器，使用新的分析模块
"""

from src.analysis.stock_analyzer import StockAnalyzer as NewStockAnalyzer

class StockAnalyzer(NewStockAnalyzer):
    """
    股票分析器类 - 向后兼容版本
    使用新的模块化分析架构
    """
    
    def __init__(self, stock_code_or_name, period="1000"):
        """
        初始化股票分析器
        :param stock_code_or_name: A股代码或公司名称，如 '000001' 或 '平安银行'
        :param period: 获取数据的天数，默认1000天
        """
        super().__init__(stock_code_or_name, period)
    
    # 保持原有的方法名以保持向后兼容
    def generate_trading_signals(self):
        """生成交易信号 - 向后兼容方法"""
        return super().generate_trading_signals()
    
    def calculate_indicators(self):
        """计算技术指标 - 向后兼容方法"""
        return super().calculate_indicators()
    
    def generate_chart(self, chart_type="comprehensive", save_path=None):
        """生成图表 - 向后兼容方法"""
        return super().generate_chart(chart_type, save_path)
    
    def print_trading_signals(self):
        """打印交易信号 - 向后兼容方法"""
        return super().print_analysis_summary()
    def __init__(self, stock_code_or_name, period="1000"):
        """
        初始化股票分析器
        :param stock_code_or_name: A股代码或公司名称，如 '000001' 或 '平安银行'
        :param period: 获取数据的天数，默认1000天
        """
        # 尝试从股票数据库获取股票代码
        try:
            from src.stock_database import stock_db
            stock_info = stock_db.get_stock_info(stock_code_or_name)
            if stock_info:
                self.stock_code = stock_info['code']
                self.stock_name = stock_info['name']
            else:
                # 如果不是公司名称，假设是股票代码
                self.stock_code = stock_code_or_name
                self.stock_name = None
        except ImportError:
            # 如果无法导入股票数据库，直接使用输入值
            self.stock_code = stock_code_or_name
            self.stock_name = None
        
        self.period = period
        self.data = None
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
            
            # 计算关键价格位
            latest_chips = chip_distribution[-1]
            
            # 找到主要筹码峰（压力位）
            peak_indices = []
            for i in range(1, len(latest_chips)-1):
                if latest_chips[i] > latest_chips[i-1] and latest_chips[i] > latest_chips[i+1]:
                    if latest_chips[i] > latest_chips.max() * 0.3:  # 只标记较大的峰
                        peak_indices.append(i)
            
            # 计算支撑位（筹码密集区域的下限）
            support_indices = []
            total_chips = np.sum(latest_chips)
            cumulative_chips = np.cumsum(latest_chips)
            
            # 找到累积筹码达到25%、50%、75%的位置作为支撑位
            for percentage in [0.25, 0.5, 0.75]:
                target_chips = total_chips * percentage
                idx = np.argmax(cumulative_chips >= target_chips)
                if idx < len(price_range):
                    support_indices.append(idx)
            
            # 计算平均价格
            weighted_avg_price = np.sum(price_range * latest_chips) / np.sum(latest_chips)
            avg_price_idx = np.argmin(np.abs(price_range - weighted_avg_price))
            
            # 保存筹码分布数据
            self.chip_data = {
                'price_range': price_range,
                'chip_distribution': chip_distribution,
                'dates': self.data['Date'].values,
                'pressure_levels': [price_range[i] for i in peak_indices],  # 压力位
                'support_levels': [price_range[i] for i in support_indices],  # 支撑位
                'avg_price': weighted_avg_price,  # 平均价格
                'current_price': self.data.iloc[-1]['Close']  # 当前价格
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
            
            # 使用自定义函数计算RSI
            self.data['RSI'] = calculate_rsi(self.data['Close'], period=14)
            
            # 使用自定义函数计算布林带
            self.data['BB_Upper'], self.data['BB_Middle'], self.data['BB_Lower'] = calculate_bollinger_bands(
                self.data['Close'], period=20, std_dev=2
            )
            
            print("技术指标计算完成")
            return True
            
        except Exception as e:
            print(f"计算技术指标失败: {e}")
            return False
    


        
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
            
            # 标记压力位（筹码峰）
            if self.chip_data['pressure_levels']:
                pressure_volumes = []
                for price in self.chip_data['pressure_levels']:
                    idx = np.argmin(np.abs(price_range - price))
                    pressure_volumes.append(chip_volumes[idx])
                
                fig.add_trace(
                    go.Scatter(
                        x=pressure_volumes,
                        y=self.chip_data['pressure_levels'],
                        mode='markers+text',
                        name='压力位',
                        text=[f'压力位<br>¥{price:.2f}' for price in self.chip_data['pressure_levels']],
                        textposition='top center',
                        marker=dict(color='red', size=10, symbol='diamond'),
                        showlegend=True
                    ),
                    row=1, col=2
                )
            
            # 标记支撑位
            if self.chip_data['support_levels']:
                support_volumes = []
                for price in self.chip_data['support_levels']:
                    idx = np.argmin(np.abs(price_range - price))
                    support_volumes.append(chip_volumes[idx])
                
                fig.add_trace(
                    go.Scatter(
                        x=support_volumes,
                        y=self.chip_data['support_levels'],
                        mode='markers+text',
                        name='支撑位',
                        text=[f'支撑位<br>¥{price:.2f}' for price in self.chip_data['support_levels']],
                        textposition='bottom center',
                        marker=dict(color='green', size=10, symbol='triangle-up'),
                        showlegend=True
                    ),
                    row=1, col=2
                )
            
            # 标记平均价格
            avg_price = self.chip_data['avg_price']
            avg_idx = np.argmin(np.abs(price_range - avg_price))
            avg_volume = chip_volumes[avg_idx]
            
            fig.add_trace(
                go.Scatter(
                    x=[avg_volume],
                    y=[avg_price],
                    mode='markers+text',
                    name='平均价格',
                    text=[f'平均价格<br>¥{avg_price:.2f}'],
                    textposition='middle right',
                    marker=dict(color='blue', size=12, symbol='star'),
                    showlegend=True
                ),
                row=1, col=2
            )
            
            # 标记当前价格
            current_price = self.chip_data['current_price']
            current_idx = np.argmin(np.abs(price_range - current_price))
            current_volume = chip_volumes[current_idx]
            
            fig.add_trace(
                go.Scatter(
                    x=[current_volume],
                    y=[current_price],
                    mode='markers+text',
                    name='当前价格',
                    text=[f'当前价格<br>¥{current_price:.2f}'],
                    textposition='middle left',
                    marker=dict(color='purple', size=12, symbol='circle'),
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

    def generate_trading_signals(self):
        """
        基于多个技术指标生成买卖信号
        综合分析MACD、RSI、布林带等指标
        """
        if self.data is None or len(self.data) < 30:
            print("数据不足，无法生成交易信号")
            return None
        
        try:
            # 获取最新数据
            latest = self.data.iloc[-1]
            previous = self.data.iloc[-2]
            
            # 初始化信号强度
            buy_signals = []
            sell_signals = []
            signal_strength = 0  # -100到100，负值表示卖出，正值表示买入
            
            # 1. MACD信号分析
            macd = latest['MACD']
            macd_signal = latest['MACD_Signal']
            macd_hist = latest['MACD_Hist']
            prev_macd_hist = previous['MACD_Hist']
            
            # MACD金叉死叉
            if macd > macd_signal and previous['MACD'] <= previous['MACD_Signal']:
                buy_signals.append("MACD金叉")
                signal_strength += 20
            elif macd < macd_signal and previous['MACD'] >= previous['MACD_Signal']:
                sell_signals.append("MACD死叉")
                signal_strength -= 20
            
            # MACD柱状图变化
            if macd_hist > 0 and macd_hist > prev_macd_hist:
                buy_signals.append("MACD柱状图增长")
                signal_strength += 10
            elif macd_hist < 0 and macd_hist < prev_macd_hist:
                sell_signals.append("MACD柱状图减少")
                signal_strength -= 10
            
            # 2. RSI信号分析
            rsi = latest['RSI']
            prev_rsi = previous['RSI']
            
            # RSI超买超卖
            if rsi < 30 and prev_rsi >= 30:
                buy_signals.append("RSI超卖反弹")
                signal_strength += 25
            elif rsi > 70 and prev_rsi <= 70:
                sell_signals.append("RSI超买回调")
                signal_strength -= 25
            
            # RSI趋势
            if rsi > 50 and rsi > prev_rsi:
                buy_signals.append("RSI上升趋势")
                signal_strength += 5
            elif rsi < 50 and rsi < prev_rsi:
                sell_signals.append("RSI下降趋势")
                signal_strength -= 5
            
            # 3. 布林带信号分析
            close_price = latest['Close']
            bb_upper = latest['BB_Upper']
            bb_lower = latest['BB_Lower']
            bb_middle = latest['BB_Middle']
            prev_close = previous['Close']
            
            # 布林带突破
            if close_price > bb_upper and prev_close <= previous['BB_Upper']:
                sell_signals.append("突破布林上轨")
                signal_strength -= 15
            elif close_price < bb_lower and prev_close >= previous['BB_Lower']:
                buy_signals.append("跌破布林下轨")
                signal_strength += 15
            
            # 布林带回归
            if close_price < bb_middle and prev_close >= previous['BB_Middle']:
                sell_signals.append("跌破布林中轨")
                signal_strength -= 10
            elif close_price > bb_middle and prev_close <= previous['BB_Middle']:
                buy_signals.append("突破布林中轨")
                signal_strength += 10
            
            # 4. 价格趋势分析
            # 计算短期和长期移动平均线
            ma5 = self.data['Close'].rolling(window=5).mean().iloc[-1]
            ma10 = self.data['Close'].rolling(window=10).mean().iloc[-1]
            ma20 = self.data['Close'].rolling(window=20).mean().iloc[-1]
            
            prev_ma5 = self.data['Close'].rolling(window=5).mean().iloc[-2]
            prev_ma10 = self.data['Close'].rolling(window=10).mean().iloc[-2]
            
            # 均线排列
            if ma5 > ma10 > ma20:
                buy_signals.append("均线多头排列")
                signal_strength += 10
            elif ma5 < ma10 < ma20:
                sell_signals.append("均线空头排列")
                signal_strength -= 10
            
            # 5. 成交量分析
            volume = latest['Volume']
            avg_volume = self.data['Volume'].rolling(window=20).mean().iloc[-1]
            
            if volume > avg_volume * 1.5 and close_price > prev_close:
                buy_signals.append("放量上涨")
                signal_strength += 10
            elif volume > avg_volume * 1.5 and close_price < prev_close:
                sell_signals.append("放量下跌")
                signal_strength -= 10
            
            # 6. 筹码分布分析
            chip_analysis = ""
            chip_signal = 0
            main_chip_price = 0
            chip_concentration = 0
            pressure_levels = []
            support_levels = []
            avg_price = 0
            
            if self.chip_data is not None:
                latest_chips = self.chip_data['chip_distribution'][-1]
                price_range = self.chip_data['price_range']
                
                # 获取关键价格位
                pressure_levels = self.chip_data['pressure_levels']
                support_levels = self.chip_data['support_levels']
                avg_price = self.chip_data['avg_price']
                current_price = float(latest['Close'])
                
                # 找到主要筹码峰
                max_chip_idx = np.argmax(latest_chips)
                main_chip_price = price_range[max_chip_idx]
                
                # 计算筹码集中度
                chip_concentration = np.max(latest_chips) / np.sum(latest_chips) * 100
                
                # 分析当前价格与关键位置的关系
                nearest_pressure = min(pressure_levels, key=lambda x: abs(x - current_price)) if pressure_levels else None
                nearest_support = min(support_levels, key=lambda x: abs(x - current_price)) if support_levels else None
                
                # 筹码分布信号
                if nearest_pressure and current_price > nearest_pressure * 0.98:
                    chip_analysis = f"价格接近压力位(¥{nearest_pressure:.2f})，可能面临阻力"
                    chip_signal = -15
                    sell_signals.append(f"接近压力位¥{nearest_pressure:.2f}")
                elif nearest_support and current_price < nearest_support * 1.02:
                    chip_analysis = f"价格接近支撑位(¥{nearest_support:.2f})，可能获得支撑"
                    chip_signal = 15
                    buy_signals.append(f"接近支撑位¥{nearest_support:.2f}")
                elif current_price > avg_price * 1.05:
                    chip_analysis = f"价格高于平均成本(¥{avg_price:.2f})，获利盘较多"
                    chip_signal = -5
                    sell_signals.append("价格高于平均成本")
                elif current_price < avg_price * 0.95:
                    chip_analysis = f"价格低于平均成本(¥{avg_price:.2f})，套牢盘较多"
                    chip_signal = 5
                    buy_signals.append("价格低于平均成本")
                else:
                    chip_analysis = f"价格在平均成本(¥{avg_price:.2f})附近，关注突破方向"
                    chip_signal = 0
                
                # 筹码集中度分析
                if chip_concentration > 15:
                    chip_analysis += "，筹码高度集中"
                    if chip_signal > 0:
                        chip_signal += 5
                    elif chip_signal < 0:
                        chip_signal -= 5
                elif chip_concentration < 5:
                    chip_analysis += "，筹码分散"
                    chip_signal = 0  # 筹码分散时信号减弱
            
            # 将筹码信号加入总信号强度
            signal_strength += chip_signal
            
            # 7. 综合信号判断
            signal_type = "观望"
            signal_description = "无明显信号"
            
            if signal_strength >= 30:
                signal_type = "强烈买入"
                signal_description = "多个指标显示强烈买入信号"
            elif signal_strength >= 15:
                signal_type = "买入"
                signal_description = "指标显示买入信号"
            elif signal_strength <= -30:
                signal_type = "强烈卖出"
                signal_description = "多个指标显示强烈卖出信号"
            elif signal_strength <= -15:
                signal_type = "卖出"
                signal_description = "指标显示卖出信号"
            else:
                signal_type = "观望"
                signal_description = "信号不明确，建议观望"
            
            # 7. 风险提示
            risk_level = "低"
            risk_description = ""
            
            if abs(signal_strength) >= 40:
                risk_level = "高"
                risk_description = "信号强度较高，请注意风险控制"
            elif abs(signal_strength) >= 20:
                risk_level = "中"
                risk_description = "信号强度中等，建议谨慎操作"
            else:
                risk_level = "低"
                risk_description = "信号强度较低，建议观望"
            
            # 8. 生成交易信号专用图表
            chart_file = self.generate_signals_chart()
            
            # 9. 生成详细报告
            report = {
                'date': latest['Date'].strftime('%Y-%m-%d %H:%M' if self.time_period != 'daily' else '%Y-%m-%d'),
                'price': f"{close_price:.2f}",
                'signal_type': signal_type,
                'signal_strength': signal_strength,
                'signal_description': signal_description,
                'risk_level': risk_level,
                'risk_description': risk_description,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'chart_file': chart_file,
                'analysis_process': {
                    'macd_analysis': {
                        'current_macd': f"{macd:.4f}",
                        'current_signal': f"{macd_signal:.4f}",
                        'current_histogram': f"{macd_hist:.4f}",
                        'previous_macd': f"{previous['MACD']:.4f}",
                        'previous_signal': f"{previous['MACD_Signal']:.4f}",
                        'previous_histogram': f"{prev_macd_hist:.4f}",
                        'trend': "多头" if macd > macd_signal else "空头",
                        'crossover': "金叉" if macd > macd_signal and previous['MACD'] <= previous['MACD_Signal'] else "死叉" if macd < macd_signal and previous['MACD'] >= previous['MACD_Signal'] else "无",
                        'histogram_trend': "增长" if macd_hist > 0 and macd_hist > prev_macd_hist else "减少" if macd_hist < 0 and macd_hist < prev_macd_hist else "平稳"
                    },
                    'rsi_analysis': {
                        'current_rsi': f"{rsi:.2f}",
                        'previous_rsi': f"{prev_rsi:.2f}",
                        'status': "超买" if rsi > 70 else "超卖" if rsi < 30 else "正常",
                        'trend': "上升" if rsi > prev_rsi else "下降",
                        'position': "强势区" if rsi > 50 else "弱势区"
                    },
                    'bollinger_analysis': {
                        'current_price': f"{close_price:.2f}",
                        'previous_price': f"{prev_close:.2f}",
                        'upper_band': f"{bb_upper:.2f}",
                        'middle_band': f"{bb_middle:.2f}",
                        'lower_band': f"{bb_lower:.2f}",
                        'position': "上轨" if close_price > bb_upper else "下轨" if close_price < bb_lower else "中轨",
                        'breakout': "向上突破" if close_price > bb_upper and prev_close <= previous['BB_Upper'] else "向下突破" if close_price < bb_lower and prev_close >= previous['BB_Lower'] else "无突破"
                    },
                    'moving_average_analysis': {
                        'ma5': f"{ma5:.2f}",
                        'ma10': f"{ma10:.2f}",
                        'ma20': f"{ma20:.2f}",
                        'arrangement': "多头排列" if ma5 > ma10 > ma20 else "空头排列" if ma5 < ma10 < ma20 else "混乱排列",
                        'price_vs_ma20': "高于20日均线" if close_price > ma20 else "低于20日均线"
                    },
                    'volume_analysis': {
                        'current_volume': f"{volume:,.0f}",
                        'average_volume': f"{avg_volume:,.0f}",
                        'volume_ratio': f"{volume/avg_volume:.2f}",
                        'volume_status': "放量" if volume > avg_volume * 1.5 else "缩量" if volume < avg_volume * 0.5 else "正常",
                        'price_volume_match': "量价配合" if (volume > avg_volume * 1.5 and close_price > prev_close) or (volume > avg_volume * 1.5 and close_price < prev_close) else "量价背离"
                    },
                    'chip_analysis': {
                        'main_chip_price': f"{main_chip_price:.2f}" if self.chip_data is not None else "无数据",
                        'current_price': f"{close_price:.2f}",
                        'avg_price': f"{avg_price:.2f}" if self.chip_data is not None else "无数据",
                        'pressure_levels': [f"{p:.2f}" for p in pressure_levels[:3]] if pressure_levels else [],
                        'support_levels': [f"{p:.2f}" for p in support_levels[:3]] if support_levels else [],
                        'price_position': "接近压力位" if nearest_pressure and close_price > nearest_pressure * 0.98 else "接近支撑位" if nearest_support and close_price < nearest_support * 1.02 else "在平均成本附近",
                        'chip_concentration': f"{chip_concentration:.1f}%" if self.chip_data is not None else "无数据",
                        'concentration_status': "高度集中" if self.chip_data is not None and chip_concentration > 15 else "分散" if self.chip_data is not None and chip_concentration < 5 else "正常",
                        'analysis': chip_analysis
                    }
                },
                'data_source': {
                    'period': self._get_period_name(),
                    'data_points': len(self.data),
                    'date_range': f"{self.data.iloc[0]['Date'].strftime('%Y-%m-%d')} 至 {self.data.iloc[-1]['Date'].strftime('%Y-%m-%d')}",
                    'calculation_method': {
                        'macd': "12日EMA - 26日EMA，信号线为9日EMA",
                        'rsi': "14日相对强弱指数",
                        'bollinger': "20日移动平均线 ± 2倍标准差",
                        'moving_average': "5日、10日、20日简单移动平均线",
                        'volume': "20日成交量移动平均",
                        'chip_distribution': "基于成交量和价格区间的筹码分布计算，衰减因子0.95"
                    }
                },
                'indicators': {
                    'macd': {
                        'value': f"{macd:.4f}",
                        'signal': f"{macd_signal:.4f}",
                        'histogram': f"{macd_hist:.4f}",
                        'trend': "多头" if macd > macd_signal else "空头"
                    },
                    'rsi': {
                        'value': f"{rsi:.2f}",
                        'status': "超买" if rsi > 70 else "超卖" if rsi < 30 else "正常"
                    },
                    'bollinger': {
                        'position': "上轨" if close_price > bb_upper else "下轨" if close_price < bb_lower else "中轨",
                        'upper': f"{bb_upper:.2f}",
                        'middle': f"{bb_middle:.2f}",
                        'lower': f"{bb_lower:.2f}"
                    },
                    'volume': {
                        'current': f"{volume:,.0f}",
                        'average': f"{avg_volume:,.0f}",
                        'ratio': f"{volume/avg_volume:.2f}"
                    }
                }
            }
            
            return report
        except Exception as e:
            print(f"生成交易信号失败: {e}")
            return None
    
    def generate_signals_chart(self):
        """生成交易信号专用图表"""
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            import plotly.express as px
            
            # 限制为最近两个月的数据
            from datetime import datetime, timedelta
            two_months_ago = datetime.now() - timedelta(days=60)
            
            # 过滤最近两个月的数据
            recent_data = self.data[self.data['Date'] >= two_months_ago].copy()
            
            if len(recent_data) == 0:
                # 如果没有最近两个月的数据，使用最后60个数据点
                recent_data = self.data.tail(60).copy()
            
            # 剔除非交易日数据（周末和节假日）
            # 只保留有交易数据的日期
            recent_data = recent_data[recent_data['Volume'] > 0].copy()
            
            # 重置索引
            recent_data = recent_data.reset_index(drop=True)
            
            # 创建子图布局 - MACD放在首位，使用垂直滑动条
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('MACD', '价格与布林带', 'RSI'),
                vertical_spacing=0.08,  # 减少垂直间距
                row_heights=[0.35, 0.35, 0.3]  # 调整各图表高度比例，让RSI有更多空间
            )
    
    # 获取数据
            dates = recent_data['Date']  # 使用实际日期
            prices = recent_data['Close']
            bb_upper = recent_data['BB_Upper']
            bb_middle = recent_data['BB_Middle']
            bb_lower = recent_data['BB_Lower']
            macd = recent_data['MACD']
            macd_signal = recent_data['MACD_Signal']
            macd_hist = recent_data['MACD_Hist']
            rsi = recent_data['RSI']
            
            # 1. MACD - 放在首位
            fig.add_trace(
                go.Scatter(
                    x=dates, y=macd,
                    mode='lines',
                    name='MACD',
                    line=dict(color='blue', width=2),
                    showlegend=False
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=dates, y=macd_signal,
                    mode='lines',
                    name='MACD信号线',
                    line=dict(color='red', width=2),
                    showlegend=False
                ),
                row=1, col=1
            )
            
            # MACD柱状图
            colors = ['red' if val >= 0 else 'green' for val in macd_hist]
            fig.add_trace(
                go.Bar(
                    x=dates, y=macd_hist,
                    name='MACD柱状图',
                    marker_color=colors,
                    opacity=0.7,
                    showlegend=False
                ),
                row=1, col=1
            )
            
            # MACD零线
            fig.add_hline(y=0, line_dash="dash", line_color="black", 
                         annotation_text="零线", row=1, col=1)
            
            # 2. 价格与布林带 - 使用蜡烛图
            fig.add_trace(
                go.Candlestick(
                    x=dates,
                    open=recent_data['Open'],
                    high=recent_data['High'],
                    low=recent_data['Low'],
                    close=recent_data['Close'],
                    name='K线',
                    increasing_line_color='red',
                    decreasing_line_color='green'
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=dates, y=bb_upper,
                    mode='lines',
                    name='布林上轨',
                    line=dict(color='rgba(255,0,0,0.3)', width=1),
                    showlegend=False
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=dates, y=bb_middle,
                    mode='lines',
                    name='布林中轨',
                    line=dict(color='blue', width=1),
                    showlegend=False
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=dates, y=bb_lower,
                    mode='lines',
                    name='布林下轨',
                    line=dict(color='rgba(255,0,0,0.3)', width=1),
                    fill='tonexty',
                    fillcolor='rgba(0,100,80,0.1)',
                    showlegend=False
                ),
                row=2, col=1
            )
            
            # 3. RSI
            fig.add_trace(
                go.Scatter(
                    x=dates, y=rsi,
                    mode='lines',
                    name='RSI',
                    line=dict(color='purple', width=2),
                    showlegend=False
                ),
                row=3, col=1
            )
            
            # RSI超买超卖线
            fig.add_hline(y=70, line_dash="dash", line_color="red", 
                         annotation_text="超买线(70)", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", 
                         annotation_text="超卖线(30)", row=3, col=1)
            
            # 更新布局
            fig.update_layout(
                title=f'{self.stock_name} 交易信号分析图表 (最近两个月)',
                height=1400,  # 减少总高度
                width=860,   # 调整宽度为860px
                showlegend=True,
                template='plotly_white',
                xaxis_rangeslider_visible=False,  # 禁用范围滑块，使用垂直滑动条
                dragmode='pan',  # 启用拖拽模式
                hovermode='x unified',  # 统一悬停模式
                # 调整边距，让图表充分利用空间
                margin=dict(l=50, r=50, t=80, b=50),
                # 为每个子图添加边框
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            # 配置x轴日期标注 - 隐藏横坐标标题，添加边框
            fig.update_xaxes(
                rangeslider_visible=False, 
                row=1, col=1,
                title_text="",  # 隐藏标题
                tickformat='%Y-%m-%d',
                tickmode='auto',
                nticks=8,
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1,
                showline=True,
                linecolor='black',
                linewidth=1
            )
            fig.update_xaxes(
                rangeslider_visible=False, 
                row=2, col=1,
                title_text="",  # 隐藏标题
                tickformat='%Y-%m-%d',
                tickmode='auto',
                nticks=8,
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1,
                showline=True,
                linecolor='black',
                linewidth=1
            )
            fig.update_xaxes(
                rangeslider_visible=False, 
                row=3, col=1,
                title_text="",  # 隐藏标题
                tickformat='%Y-%m-%d',
                tickmode='auto',
                nticks=8,
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1,
                showline=True,
                linecolor='black',
                linewidth=1
            )
            
            # 配置y轴标题和边框
            fig.update_yaxes(
                title_text="MACD", 
                row=1, col=1,
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1,
                showline=True,
                linecolor='black',
                linewidth=1
            )
            fig.update_yaxes(
                title_text="价格 (¥)", 
                row=2, col=1,
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1,
                showline=True,
                linecolor='black',
                linewidth=1
            )
            fig.update_yaxes(
                title_text="RSI", 
                row=3, col=1,
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1,
                showline=True,
                linecolor='black',
                linewidth=1
            )
            
            # 移除MACD副坐标轴配置，使用标准布局
            
            # 添加交互配置
            fig.update_layout(
                # 启用缩放和平移
                modebar=dict(
                    orientation='v',
                    bgcolor='rgba(255,255,255,0.8)',
                    color='black',
                    activecolor='#667eea'
                ),
                # 配置选择工具
                selectdirection='any'
            )
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.stock_code}_signals_{timestamp}.html"
            
            # 确保输出目录存在
            os.makedirs('output', exist_ok=True)
            filepath = os.path.join('output', filename)
        
        # 保存图表
            fig.write_html(filepath)
            
            return filename
            
        except Exception as e:
            print(f"生成交易信号图表时出错: {e}")
            return None
    
    def print_trading_signals(self):
        """打印交易信号分析"""
        report = self.generate_trading_signals()
        if report is None:
            return
        
        print(f"\n{'='*60}")
        print(f"📊 {self.stock_code} ({self.stock_name}) 交易信号分析")
        print(f"{'='*60}")
        print(f"📅 分析时间: {report['date']}")
        print(f"💰 当前价格: {report['price']}")
        print(f"🎯 信号类型: {report['signal_type']}")
        print(f"📈 信号强度: {report['signal_strength']}")
        print(f"📝 信号描述: {report['signal_description']}")
        print(f"⚠️  风险等级: {report['risk_level']}")
        print(f"💡 风险提示: {report['risk_description']}")
        
        if report['buy_signals']:
            print(f"\n🟢 买入信号:")
            for signal in report['buy_signals']:
                print(f"   ✅ {signal}")
        
        if report['sell_signals']:
            print(f"\n🔴 卖出信号:")
            for signal in report['sell_signals']:
                print(f"   ❌ {signal}")
        
        print(f"\n📊 技术指标详情:")
        indicators = report['indicators']
        print(f"   MACD: {indicators['macd']['value']} | 信号线: {indicators['macd']['signal']} | 趋势: {indicators['macd']['trend']}")
        print(f"   RSI: {indicators['rsi']['value']} ({indicators['rsi']['status']})")
        print(f"   布林带: 价格在{indicators['bollinger']['position']} | 上轨:{indicators['bollinger']['upper']} | 下轨:{indicators['bollinger']['lower']}")
        print(f"   成交量: {indicators['volume']['current']} (平均:{indicators['volume']['average']}, 比率:{indicators['volume']['ratio']})")
        
        print(f"\n💡 投资建议:")
        if report['signal_type'] in ["强烈买入", "买入"]:
            print("   🟢 可以考虑买入，注意设置止损")
        elif report['signal_type'] in ["强烈卖出", "卖出"]:
            print("   🔴 可以考虑卖出，注意控制风险")
        else:
            print("   🟡 建议观望，等待更明确的信号")
        
        print(f"{'='*60}")

 