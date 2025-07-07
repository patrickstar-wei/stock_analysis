import React, { useEffect, useRef, useState } from 'react';
import { 
  createChart, 
  ColorType,
  CandlestickSeries,
  HistogramSeries,
  LineSeries
} from 'lightweight-charts';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
} from '@mui/material';

const TradingViewChart = ({ allStockData, stockInfo, allSignals }) => {
  const [selectedPeriod, setSelectedPeriod] = useState('daily');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [initAttempts, setInitAttempts] = useState(0);

  const priceChartContainerRef = useRef(null);
  const volumeChartContainerRef = useRef(null);
  const macdChartContainerRef = useRef(null);
  
  const priceChartRef = useRef(null);
  const volumeChartRef = useRef(null);
  const macdChartRef = useRef(null);

  const handlePeriodChange = (event, newPeriod) => {
    if (newPeriod !== null) {
      setSelectedPeriod(newPeriod);
    }
  };

  // 获取当前选中周期的数据
  const stockData = allStockData?.[selectedPeriod] || [];

  // 强制重新初始化的函数
  const forceInit = () => {
    setInitAttempts(prev => prev + 1);
    setLoading(true);
    setError(null);
  };

  useEffect(() => {
    console.log('=== TradingViewChart useEffect ===');
    console.log('Stock data available:', !!stockData, 'Length:', stockData?.length);
    console.log('Init attempts:', initAttempts);
    console.log('Current state - loading:', loading, 'error:', !!error);
    
    if (!stockData || stockData.length === 0) {
      console.log('No stock data, setting loading to false');
      setLoading(false);
      return;
    }

    // 清理之前的图表
    [priceChartRef, volumeChartRef, macdChartRef].forEach(chartRef => {
      if (chartRef.current) {
        try {
          chartRef.current.remove();
        } catch (error) {
          console.warn('Chart cleanup warning:', error);
        }
        chartRef.current = null;
      }
    });

    // 设置loading为false，让容器先渲染出来
    setLoading(false);
    setError(null);

    // 使用更激进的方法：多次重试 + DOM查询
    const maxRetries = 15;
    let retryCount = 0;
    
    const tryInitialize = () => {
      retryCount++;
      console.log(`Starting container check (attempt ${retryCount}/${maxRetries})...`);
      
      // 同时使用ref和DOM查询两种方式
      const priceElRef = priceChartContainerRef.current;
      const volumeElRef = volumeChartContainerRef.current;
      const macdElRef = macdChartContainerRef.current;
      
      // 备用：通过类名查找容器（因为它们有独特的样式）
      const allDivs = document.querySelectorAll('div[style*="background-color: rgb(37, 40, 54)"]');
      console.log('Found divs with background color:', allDivs.length);
      
      // 更精确的查找：通过样式组合查找
      const priceElDOM = Array.from(allDivs).find(div => 
        div.style.height === '400px' && 
        div.style.backgroundColor === 'rgb(37, 40, 54)'
      );
      const volumeElDOM = Array.from(allDivs).find(div => 
        div.style.height === '200px' && 
        div.style.backgroundColor === 'rgb(37, 40, 54)' &&
        div !== priceElDOM
      );
      const macdElDOM = Array.from(allDivs).find(div => 
        div.style.height === '200px' && 
        div.style.backgroundColor === 'rgb(37, 40, 54)' &&
        div !== priceElDOM &&
        div !== volumeElDOM
      );
      
      const priceEl = priceElRef || priceElDOM;
      const volumeEl = volumeElRef || volumeElDOM;
      const macdEl = macdElRef || macdElDOM;
      
      console.log('Container check results:', {
        attempt: retryCount,
        priceElRef: !!priceElRef,
        priceElDOM: !!priceElDOM,
        priceEl: !!priceEl,
        priceWidth: priceEl?.offsetWidth || 0,
        priceHeight: priceEl?.offsetHeight || 0,
        volumeElRef: !!volumeElRef,
        volumeElDOM: !!volumeElDOM,
        volumeEl: !!volumeEl,
        volumeWidth: volumeEl?.offsetWidth || 0,
        volumeHeight: volumeEl?.offsetHeight || 0,
        macdElRef: !!macdElRef,
        macdElDOM: !!macdElDOM,
        macdEl: !!macdEl,
        macdWidth: macdEl?.offsetWidth || 0,
        macdHeight: macdEl?.offsetHeight || 0,
        totalDivsFound: allDivs.length,
        allDivsInfo: Array.from(allDivs).map(div => ({
          height: div.style.height,
          width: div.style.width,
          backgroundColor: div.style.backgroundColor
        }))
      });

      if (!priceEl || !volumeEl || !macdEl) {
        if (retryCount < maxRetries) {
          console.log(`Containers not ready, retrying in 300ms...`);
          setTimeout(tryInitialize, 300);
          return;
        } else {
          console.error('Containers not found after all retries');
          setError('图表容器未找到，请刷新页面重试');
          return;
        }
      }

      if (priceEl.offsetWidth === 0 || volumeEl.offsetWidth === 0 || macdEl.offsetWidth === 0) {
        if (retryCount < maxRetries) {
          console.log(`Containers have zero width, retrying in 300ms...`);
          setTimeout(tryInitialize, 300);
          return;
        } else {
          console.error('Containers have zero width after all retries');
          setError('图表容器尺寸异常，请刷新页面重试');
          return;
        }
      }

      // 更新ref以确保createCharts可以使用
      if (!priceChartContainerRef.current && priceEl) priceChartContainerRef.current = priceEl;
      if (!volumeChartContainerRef.current && volumeEl) volumeChartContainerRef.current = volumeEl;
      if (!macdChartContainerRef.current && macdEl) macdChartContainerRef.current = macdEl;

      // 开始创建图表
      try {
        console.log('All containers ready, creating charts...');
        setLoading(true); // 设置loading为true，显示加载状态
        createCharts();
      } catch (error) {
        console.error('Chart creation failed:', error);
        setError(`图表创建失败: ${error.message}`);
        setLoading(false);
      }
    };
    
    // 首次尝试延迟500ms
    const initTimeout = setTimeout(tryInitialize, 500);

    return () => {
      clearTimeout(initTimeout);
    };
  }, [stockData, initAttempts, selectedPeriod]); // eslint-disable-line react-hooks/exhaustive-deps

  const createCharts = () => {
    try {
      console.log('Starting chart creation...');
      
      // ---------- 日期与字段兼容处理 ----------
      const parseDate = (value) => {
        /*
         * 支持以下格式：
         * 1. 字符串 'YYYY-MM-DD' / 'YYYY/MM/DD'
         * 2. JavaScript Date 对象
         * 3. 其他可解析的日期字符串（回退给 Date 构造函数）
         * 返回符合 Lightweight-Charts v5 BusinessDay 格式的对象：{ year, month, day }
         */
        if (!value) return undefined;

        // Date 对象
        if (value instanceof Date) {
          return {
            year: value.getFullYear(),
            month: value.getMonth() + 1, // getMonth() 从 0 开始
            day: value.getDate(),
          };
        }

        // 字符串处理
        if (typeof value === 'string') {
          // 1) 如果包含时间信息 (如 "2024-07-07 14:30:00" 或 ISO 字符串)，直接返回 Unix 时间戳（秒）
          if (value.includes(':')) {
            const d = new Date(value.replace(/-/g, '/'));
            if (!isNaN(d)) {
              return Math.floor(d.getTime() / 1000);
            }
          }

          // 2) 仅日期字符串，兼容 2024-07-07 / 2024/7/7 等形式 -> BusinessDay
          const match = value.match(/(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
          if (match) {
            return {
              year: Number(match[1]),
              month: Number(match[2]),
              day: Number(match[3]),
            };
          }

          // 3) 回退：Date 构造解析
          const d = new Date(value);
          if (!isNaN(d)) {
            return {
              year: d.getFullYear(),
              month: d.getMonth() + 1,
              day: d.getDate(),
            };
          }
        }

        return undefined; // 无法解析
      };

      // 将后端各种字段命名统一映射，过滤掉无效数据行
      const processedDataRaw = stockData
        .map((item) => {
          // 后端可能返回 Date/日期字段大小写不一致，做兼容
          const dateValue = item.date ?? item.Date ?? item.time ?? item.Time;

          return {
            rawDate: dateValue,
            time: parseDate(dateValue),
            open: parseFloat(item.open ?? item.Open),
            high: parseFloat(item.high ?? item.High),
            low: parseFloat(item.low ?? item.Low),
            close: parseFloat(item.close ?? item.Close),
            volume: parseFloat(item.volume ?? item.Volume),
          };
        })
        .filter((d) => d.time && !Number.isNaN(d.open) && !Number.isNaN(d.close));

      // ---- 排序并去除重复时间 ----
      const sortedData = [...processedDataRaw].sort((a, b) => {
        const getSec = (t, raw) => {
          if (typeof t === 'number') return t;
          if (t && t.year) return Date.UTC(t.year, t.month - 1, t.day) / 1000;
          return new Date(raw).getTime() / 1000;
        };
        return getSec(a.time, a.rawDate) - getSec(b.time, b.rawDate);
      });

      const uniqueData = [];
      const seen = new Set();
      for (const d of sortedData) {
        const key = typeof d.time === 'number' ? d.time : `${d.time.year}-${d.time.month}-${d.time.day}`;
        if (!seen.has(key)) {
          seen.add(key);
          const { rawDate, ...rest } = d; // 移除辅助字段
          uniqueData.push(rest);
        }
      }

      let processedData = uniqueData;

      // ---- 周线时间跨度限制：仅保留最近26周（约半年） ----
      if (selectedPeriod === 'weekly') {
        processedData = processedData.slice(-26);
      }

      console.log('Processed data sample:', processedData.slice(0, 3));

      // 创建主K线图表
      const priceChartResult = createChart(priceChartContainerRef.current, {
        width: priceChartContainerRef.current.offsetWidth,
        height: 400,
        layout: {
          background: { type: ColorType.Solid, color: '#253654' },
          textColor: '#DDD',
        },
        grid: {
          vertLines: { color: '#334155' },
          horzLines: { color: '#334155' },
        },
        crosshair: { mode: 1 },
        timeScale: {
          borderColor: '#485462',
          timeVisible: true,
          secondsVisible: false,
        },
        rightPriceScale: {
          borderColor: '#485462',
        },
      });
      
      console.log('Price chart result:', priceChartResult);
      console.log('Price chart result type:', typeof priceChartResult);
      console.log('Price chart result keys:', Object.keys(priceChartResult || {}));
      
      // 根据返回结果确定正确的chart对象
      let priceChart;
      if (priceChartResult && typeof priceChartResult === 'object') {
        // 检查是否有addCandlestickSeries方法（直接是ChartApi对象）
        if (typeof priceChartResult.addCandlestickSeries === 'function') {
          priceChart = priceChartResult;
        } else if (priceChartResult.chart && typeof priceChartResult.chart.addCandlestickSeries === 'function') {
          // 检查是否有.chart属性且该属性有addCandlestickSeries方法
          priceChart = priceChartResult.chart;
        } else {
          // 检查原型链上的方法
          const proto = Object.getPrototypeOf(priceChartResult);
          if (proto && typeof proto.addCandlestickSeries === 'function') {
            priceChart = priceChartResult;
          } else if (proto && typeof proto.addSeries === 'function') {
            // 如果没有addCandlestickSeries，但有addSeries，尝试使用addSeries
            console.log('Using addSeries instead of addCandlestickSeries');
            priceChart = priceChartResult;
          } else {
            console.error('Unexpected priceChartResult structure:', priceChartResult);
            console.error('Available methods:', Object.getOwnPropertyNames(priceChartResult));
            console.error('Prototype methods:', proto ? Object.getOwnPropertyNames(proto) : 'No prototype');
            throw new Error('无法创建价格图表：返回对象结构异常');
          }
        }
      } else {
        console.error('priceChartResult is not an object:', priceChartResult);
        throw new Error('无法创建价格图表：返回结果异常');
      }

      // 创建K线图
      let candlestickSeries;
      if (typeof priceChart.addCandlestickSeries === 'function') {
        candlestickSeries = priceChart.addCandlestickSeries({
          // A股颜色规范：涨红跌绿
          upColor: '#ff4976',
          downColor: '#00ff88',
          borderUpColor: '#ff4976',
          borderDownColor: '#00ff88',
          wickUpColor: '#ff4976',
          wickDownColor: '#00ff88',
        });
      } else if (typeof priceChart.addSeries === 'function') {
        // 使用addSeries方法创建K线图
        candlestickSeries = priceChart.addSeries(CandlestickSeries, {
          upColor: '#ff4976',
          downColor: '#00ff88',
          borderUpColor: '#ff4976',
          borderDownColor: '#00ff88',
          wickUpColor: '#ff4976',
          wickDownColor: '#00ff88',
        });
      } else {
        throw new Error('无法创建K线图：不支持的方法');
      }

      candlestickSeries.setData(processedData);

      // 添加移动平均线
      const ma5Data = calculateMA(processedData, 5);
      const ma10Data = calculateMA(processedData, 10);
      const ma20Data = calculateMA(processedData, 20);

      if (ma5Data.length > 0) {
        let ma5Series;
        if (typeof priceChart.addLineSeries === 'function') {
          ma5Series = priceChart.addLineSeries({
            color: '#ffeb3b',
            lineWidth: 1,
            title: 'MA5',
          });
        } else if (typeof priceChart.addSeries === 'function') {
          ma5Series = priceChart.addSeries(LineSeries, {
            color: '#ffeb3b',
            lineWidth: 1,
            title: 'MA5',
          });
        } else {
          throw new Error('无法创建MA5线：不支持的方法');
        }
        ma5Series.setData(ma5Data);
      }

      if (ma10Data.length > 0) {
        let ma10Series;
        if (typeof priceChart.addLineSeries === 'function') {
          ma10Series = priceChart.addLineSeries({
            color: '#2196f3',
            lineWidth: 1,
            title: 'MA10',
          });
        } else if (typeof priceChart.addSeries === 'function') {
          ma10Series = priceChart.addSeries(LineSeries, {
            color: '#2196f3',
            lineWidth: 1,
            title: 'MA10',
          });
        } else {
          throw new Error('无法创建MA10线：不支持的方法');
        }
        ma10Series.setData(ma10Data);
      }

      if (ma20Data.length > 0) {
        let ma20Series;
        if (typeof priceChart.addLineSeries === 'function') {
          ma20Series = priceChart.addLineSeries({
            color: '#f44336',
            lineWidth: 1,
            title: 'MA20',
          });
        } else if (typeof priceChart.addSeries === 'function') {
          ma20Series = priceChart.addSeries(LineSeries, {
            color: '#f44336',
            lineWidth: 1,
            title: 'MA20',
          });
        } else {
          throw new Error('无法创建MA20线：不支持的方法');
        }
        ma20Series.setData(ma20Data);
      }

      // 创建成交量图表
      const volumeChartResult = createChart(volumeChartContainerRef.current, {
        width: volumeChartContainerRef.current.offsetWidth,
        height: 200,
        layout: {
          background: { type: ColorType.Solid, color: '#253654' },
          textColor: '#DDD',
        },
        grid: {
          vertLines: { color: '#334155' },
          horzLines: { color: '#334155' },
        },
        crosshair: { mode: 1 },
        timeScale: {
          borderColor: '#485462',
          timeVisible: true,
          secondsVisible: false,
        },
        rightPriceScale: {
          borderColor: '#485462',
        },
      });
      
      // 根据返回结果确定正确的chart对象（兼容v5无addHistogramSeries的情况）
      let volumeChart;
      if (volumeChartResult && typeof volumeChartResult === 'object') {
        if (typeof volumeChartResult.addHistogramSeries === 'function') {
          // v4/v3 旧API
          volumeChart = volumeChartResult;
        } else if (typeof volumeChartResult.addSeries === 'function') {
          // v5 新API，仅提供 addSeries
          volumeChart = volumeChartResult;
        } else if (volumeChartResult.chart && (typeof volumeChartResult.chart.addHistogramSeries === 'function' || typeof volumeChartResult.chart.addSeries === 'function')) {
          // 某些打包工具可能包在 .chart 属性下
          volumeChart = volumeChartResult.chart;
        } else {
          const proto = Object.getPrototypeOf(volumeChartResult);
          if (proto && (typeof proto.addHistogramSeries === 'function' || typeof proto.addSeries === 'function')) {
            volumeChart = volumeChartResult;
          } else {
            console.error('Unexpected volumeChartResult structure:', volumeChartResult);
            console.error('Available methods:', Object.getOwnPropertyNames(volumeChartResult));
            console.error('Prototype methods:', proto ? Object.getOwnPropertyNames(proto) : 'No prototype');
            throw new Error('无法创建成交量图表：返回对象结构异常');
          }
        }
      } else {
        console.error('volumeChartResult is not an object:', volumeChartResult);
        throw new Error('无法创建成交量图表：返回结果异常');
      }

      const volumeData = processedData.map(item => ({
        time: item.time,
        value: item.volume,
        // A股规范：涨红跌绿
        color: item.close >= item.open ? '#ff497640' : '#00ff8840'
      }));

      let volumeSeries;
      if (typeof volumeChart.addHistogramSeries === 'function') {
        volumeSeries = volumeChart.addHistogramSeries({
          color: '#26a69a',
          priceFormat: {
            type: 'volume',
          },
          priceScaleId: '',
          scaleMargins: {
            top: 0.8,
            bottom: 0,
          },
        });
      } else if (typeof volumeChart.addSeries === 'function') {
        // 使用addSeries方法创建成交量图
        volumeSeries = volumeChart.addSeries(HistogramSeries, {
          color: '#26a69a',
          priceFormat: {
            type: 'volume',
          },
          priceScaleId: '',
          scaleMargins: {
            top: 0.8,
            bottom: 0,
          },
        });
      } else {
        throw new Error('无法创建成交量图：不支持的方法');
      }

      volumeSeries.setData(volumeData);

      // 创建MACD图表
      const macdChartResult = createChart(macdChartContainerRef.current, {
        width: macdChartContainerRef.current.offsetWidth,
        height: 200,
        layout: {
          background: { type: ColorType.Solid, color: '#253654' },
          textColor: '#DDD',
        },
        grid: {
          vertLines: { color: '#334155' },
          horzLines: { color: '#334155' },
        },
        crosshair: { mode: 1 },
        timeScale: {
          borderColor: '#485462',
          timeVisible: true,
          secondsVisible: false,
        },
        rightPriceScale: {
          borderColor: '#485462',
        },
      });
      
      // 根据返回结果确定正确的chart对象
      let macdChart;
      if (macdChartResult && typeof macdChartResult === 'object') {
        // 直接 ChartApi 对象 - 支持 addLineSeries 或 addSeries
        if (typeof macdChartResult.addLineSeries === 'function' || typeof macdChartResult.addSeries === 'function') {
          macdChart = macdChartResult;
        } else if (
          macdChartResult.chart &&
          (typeof macdChartResult.chart.addLineSeries === 'function' || typeof macdChartResult.chart.addSeries === 'function')
        ) {
          macdChart = macdChartResult.chart;
        } else {
          const proto = Object.getPrototypeOf(macdChartResult);
          if (proto && (typeof proto.addLineSeries === 'function' || typeof proto.addSeries === 'function')) {
            macdChart = macdChartResult;
          } else {
            console.error('Unexpected macdChartResult structure:', macdChartResult);
            console.error('Available methods:', Object.getOwnPropertyNames(macdChartResult));
            console.error('Prototype methods:', proto ? Object.getOwnPropertyNames(proto) : 'No prototype');
            throw new Error('无法创建MACD图表：返回对象结构异常');
          }
        }
      } else {
        console.error('macdChartResult is not an object:', macdChartResult);
        throw new Error('无法创建MACD图表：返回结果异常');
      }

      const macdData = calculateMACD(processedData);
      
      if (macdData.macd.length > 0) {
        let macdSeries;
        if (typeof macdChart.addLineSeries === 'function') {
          macdSeries = macdChart.addLineSeries({
            color: '#2196f3',
            lineWidth: 2,
            title: 'MACD',
          });
        } else if (typeof macdChart.addSeries === 'function') {
          macdSeries = macdChart.addSeries(LineSeries, {
            color: '#2196f3',
            lineWidth: 2,
            title: 'MACD',
          });
        } else {
          throw new Error('无法创建MACD线：不支持的方法');
        }
        macdSeries.setData(macdData.macd);
      }

      if (macdData.signal.length > 0) {
        let signalSeries;
        if (typeof macdChart.addLineSeries === 'function') {
          signalSeries = macdChart.addLineSeries({
            color: '#ff9800',
            lineWidth: 2,
            title: 'Signal',
          });
        } else if (typeof macdChart.addSeries === 'function') {
          signalSeries = macdChart.addSeries(LineSeries, {
            color: '#ff9800',
            lineWidth: 2,
            title: 'Signal',
          });
        } else {
          throw new Error('无法创建Signal线：不支持的方法');
        }
        signalSeries.setData(macdData.signal);
      }

      if (macdData.histogram.length > 0) {
        // 为柱状图设置涨红跌绿颜色
        const histogramWithColor = macdData.histogram.map(item => ({
          ...item,
          color: item.value >= 0 ? '#ff4976' : '#00ff88'
        }));

        let histogramSeries;
        if (typeof macdChart.addHistogramSeries === 'function') {
          histogramSeries = macdChart.addHistogramSeries({
            base: 0,
            priceFormat: { type: 'price' },
            lineWidth: 1,
            title: 'Histogram',
          });
        } else if (typeof macdChart.addSeries === 'function') {
          histogramSeries = macdChart.addSeries(HistogramSeries, {
            base: 0,
            priceFormat: { type: 'price' },
            lineWidth: 1,
            title: 'Histogram',
          });
        } else {
          throw new Error('无法创建Histogram：不支持的方法');
        }
        histogramSeries.setData(histogramWithColor);
      }

      // 保存图表引用
      priceChartRef.current = priceChart;
      volumeChartRef.current = volumeChart;
      macdChartRef.current = macdChart;

      // ---------- 初始时间范围同步 ----------
      try {
        // 1) 先让主图完整显示全部数据
        priceChart.timeScale().fitContent();

        // 2) 获取主图可见逻辑范围并应用到其他图表
        const initialLogical = priceChart.timeScale().getVisibleLogicalRange();
        if (initialLogical) {
          volumeChart.timeScale().setVisibleLogicalRange(initialLogical);
          macdChart.timeScale().setVisibleLogicalRange(initialLogical);
        }
      } catch (e) {
        console.warn('初始时间范围同步失败:', e);
      }

      // ---------- 动态同步时间轴 ----------
      priceChart.timeScale().subscribeVisibleLogicalRangeChange(() => {
        const logical = priceChart.timeScale().getVisibleLogicalRange();
        if (!logical) return;
        try {
          volumeChart.timeScale().setVisibleLogicalRange(logical);
          macdChart.timeScale().setVisibleLogicalRange(logical);
        } catch (e) {
          console.warn('同步时间轴失败:', e);
        }
      });

      console.log('Charts created successfully');
      setLoading(false);
      setError(null);
    } catch (error) {
      console.error('Chart creation error:', error);
      setError(`图表创建失败: ${error.message}`);
      setLoading(false);
    }
  };

  const calculateMA = (data, period) => {
    const result = [];
    for (let i = period - 1; i < data.length; i++) {
      const slice = data.slice(i - period + 1, i + 1);
      const sum = slice.reduce((acc, item) => acc + item.close, 0);
      result.push({
        time: data[i].time,
        value: sum / period
      });
    }
    return result;
  };

  const calculateMACD = (data, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) => {
    if (data.length < slowPeriod) {
      return { macd: [], signal: [], histogram: [] };
    }

    const prices = data.map(item => item.close);
    const fastEMA = calculateEMAFromValues(prices, fastPeriod);
    const slowEMA = calculateEMAFromValues(prices, slowPeriod);
    
    const macdLine = [];
    const startIndex = slowPeriod - 1;
    
    for (let i = startIndex; i < data.length; i++) {
      const macdValue = fastEMA[i] - slowEMA[i];
      macdLine.push(macdValue);
    }
    
    const signalLine = calculateEMAFromValues(macdLine, signalPeriod);
    
    const macd = [];
    const signal = [];
    const histogram = [];
    
    const signalStartIndex = startIndex + signalPeriod - 1;
    
    for (let i = signalStartIndex; i < data.length; i++) {
      const macdIndex = i - startIndex;
      const signalIndex = i - signalStartIndex;
      
      if (macdIndex < macdLine.length && signalIndex < signalLine.length) {
        macd.push({
          time: data[i].time,
          value: macdLine[macdIndex]
        });
        
        signal.push({
          time: data[i].time,
          value: signalLine[signalIndex]
        });
        
        histogram.push({
          time: data[i].time,
          value: macdLine[macdIndex] - signalLine[signalIndex]
        });
      }
    }
    
    return { macd, signal, histogram };
  };

  const calculateEMAFromValues = (data, period) => {
    const result = [];
    const multiplier = 2 / (period + 1);
    
    let ema = data[0];
    result.push(ema);
    
    for (let i = 1; i < data.length; i++) {
      ema = (data[i] * multiplier) + (ema * (1 - multiplier));
      result.push(ema);
    }
    
    return result;
  };

  if (!allStockData || Object.keys(allStockData).length === 0) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="info">
          暂无图表数据，请先生成交易信号
        </Alert>
      </Box>
    );
  }

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ p: 0, flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* 股票信息 - 固定在顶部 */}
        <Box sx={{ p: 2, bgcolor: 'info.50', borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6" color="info.main" gutterBottom>
            📈 {stockInfo?.name || '股票'} 技术图表
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {stockInfo?.code && (
              <Chip label={`代码: ${stockInfo.code}`} size="small" />
            )}
            {stockInfo?.current_price && (
              <Chip 
                label={`当前价: ¥${stockInfo.current_price}`} 
                size="small"
                color={stockInfo.change_percent > 0 ? 'success' : 'error'}
              />
            )}
            {stockInfo?.change_percent && (
              <Chip 
                label={`涨幅: ${stockInfo.change_percent > 0 ? '+' : ''}${stockInfo.change_percent}%`} 
                size="small"
                color={stockInfo.change_percent > 0 ? 'success' : 'error'}
              />
            )}
          </Box>
        </Box>

        {/* 周期选择器 - 二级标签 */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={selectedPeriod} 
            onChange={handlePeriodChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ minHeight: 40 }}
          >
            {Object.entries(allStockData).map(([periodKey, periodData]) => (
              <Tab 
                key={periodKey} 
                value={periodKey} 
                label={allSignals?.[periodKey]?.period_name || periodKey}
                sx={{ minHeight: 40, py: 1 }}
              />
            ))}
          </Tabs>
        </Box>

        {/* 图表内容 - 可滚动区域 */}
        <Box sx={{ flex: 1, overflow: 'auto' }}>
          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
              <CircularProgress />
              <Typography variant="body2" sx={{ ml: 2 }}>
                正在加载图表...
              </Typography>
            </Box>
          )}

          {error && (
            <Box sx={{ p: 2 }}>
              <Alert severity="error" action={
                <button onClick={forceInit}>重试</button>
              }>
                {error}
              </Alert>
            </Box>
          )}

          {!loading && !error && (
            <Box sx={{ p: 2 }}>
              <Grid container spacing={2}>
                {/* 主价格图表 */}
                <Grid item xs={12}>
                  <Paper sx={{ p: 1 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      价格走势 (含移动平均线)
                    </Typography>
                    <Box
                      ref={priceChartContainerRef}
                      sx={{
                        width: '100%',
                        height: 400,
                        backgroundColor: '#253654',
                        borderRadius: 0,
                      }}
                    />
                  </Paper>
                </Grid>

                {/* 成交量图表 */}
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 1 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      成交量
                    </Typography>
                    <Box
                      ref={volumeChartContainerRef}
                      sx={{
                        width: '100%',
                        height: 200,
                        backgroundColor: '#253654',
                        borderRadius: 0,
                      }}
                    />
                  </Paper>
                </Grid>

                {/* MACD图表 */}
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 1 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      MACD指标
                    </Typography>
                    <Box
                      ref={macdChartContainerRef}
                      sx={{
                        width: '100%',
                        height: 200,
                        backgroundColor: '#253654',
                        borderRadius: 0,
                      }}
                    />
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default TradingViewChart; 