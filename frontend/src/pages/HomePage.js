import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Paper,
  AppBar,
  Toolbar,
  Fab,
  Zoom,
} from '@mui/material';
import {
  TrendingUp,
  Analytics,
  ShowChart,
  KeyboardArrowUp,
  Info,
} from '@mui/icons-material';
import StockSearch from '../components/StockSearch';
import TradingSignals from '../components/TradingSignals';
import DetailedAnalysis from '../components/DetailedAnalysis';
import TradingViewChart from '../components/TradingViewChart';
import { fetchTradingSignals } from '../utils/api';

const HomePage = () => {
  const [stockCode, setStockCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [allSignals, setAllSignals] = useState(null);
  const [comprehensiveAdvice, setComprehensiveAdvice] = useState(null);
  const [allStockData, setAllStockData] = useState(null);
  const [stockInfo, setStockInfo] = useState(null);
  const [backtestResult, setBacktestResult] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const containerRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!stockCode || typeof stockCode !== 'string' || !stockCode.trim()) {
      setError('请输入股票代码');
      return;
    }

    setLoading(true);
    setError('');
    setAllSignals(null);
    setComprehensiveAdvice(null);
    setAllStockData(null);
    setStockInfo(null);
    setBacktestResult(null);
    setActiveTab(0);

    try {
      const response = await fetchTradingSignals(stockCode);
      
      // 检查响应格式并适配
      if (response) {
        // 如果响应有success字段，使用包装格式
        if (response.success !== undefined) {
          if (response.success) {
            // 当前后端格式：数据直接在顶层
            setAllSignals(response.all_signals);
            setComprehensiveAdvice(response.comprehensive_advice);
            setAllStockData(response.all_stock_data);
            setStockInfo(response.stock_info);
            setBacktestResult(response.backtest_result);
          } else {
            setError(response.message || '获取数据失败');
          }
        } else {
          // 直接响应格式（备用兼容）
          setAllSignals(response.all_signals);
          setComprehensiveAdvice(response.comprehensive_advice);
          setAllStockData(response.all_stock_data);
          setStockInfo(response.stock_info);
          setBacktestResult(response.backtest_result);
        }
      } else {
        setError('获取数据失败：响应为空');
      }
    } catch (err) {
      console.error('获取交易信号失败:', err);
      setError('网络错误，请检查后端服务是否启动');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  useEffect(() => {
    const handleScroll = () => {
      if (containerRef.current) {
        const scrollTop = containerRef.current.scrollTop;
        setShowScrollTop(scrollTop > 300);
      }
    };

    const container = containerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, []);

  const scrollToTop = () => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  };

  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ height: '100%' }}>
          {children}
        </Box>
      )}
    </div>
  );

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 固定顶部导航栏 */}
      <AppBar position="static" elevation={0} sx={{ bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
        <Toolbar sx={{ minHeight: 48, height: 48 }}>
          <Typography variant="h6" component="h1" sx={{ 
            background: 'linear-gradient(135deg, #90caf9 0%, #ce93d8 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontWeight: 400,
            flexGrow: 1,
            fontSize: '1.1rem'
          }}>
            📈 股票分析系统
          </Typography>
        </Toolbar>
      </AppBar>

      {/* 主内容区域 */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 左侧输入面板 - 固定宽度 */}
        <Box sx={{ width: 320, p: 2, borderRight: 1, borderColor: 'divider', bgcolor: 'background.default' }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Analytics color="primary" />
                分析参数
              </Typography>
              
              <form onSubmit={handleSubmit}>
                <Box sx={{ mb: 2 }}>
                  <StockSearch
                    value={stockCode}
                    onChange={(value) => setStockCode(typeof value === 'string' ? value : '')}
                    onSelect={(value) => setStockCode(typeof value === 'string' ? value : '')}
                  />
                </Box>

                <Button
                  type="submit"
                  variant="contained"
                  fullWidth
                  size="medium"
                  disabled={loading}
                  sx={{ 
                    py: 1,
                    background: 'linear-gradient(135deg, #90caf9 0%, #ce93d8 100%)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #64b5f6 0%, #ab47bc 100%)',
                    }
                  }}
                >
                  {loading ? (
                    <CircularProgress size={20} color="inherit" />
                  ) : (
                    <>
                      <TrendingUp sx={{ mr: 1, fontSize: '1rem' }} />
                      生成交易信号
                    </>
                  )}
                </Button>
              </form>

              {error && (
                <Alert severity="error" sx={{ mt: 2, fontSize: '0.875rem' }}>
                  {error}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Box>

        {/* 右侧分析面板 - 可滚动 */}
        <Box 
          ref={containerRef}
          sx={{ 
            flex: 1, 
            overflow: 'auto',
            bgcolor: 'background.default',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          {allSignals ? (
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              {/* 标签页导航 */}
              <Paper sx={{ m: 2, mb: 0 }}>
                <Tabs 
                  value={activeTab} 
                  onChange={handleTabChange}
                  variant="fullWidth"
                  indicatorColor="primary"
                  textColor="primary"
                >
                  <Tab 
                    label="交易信号" 
                    icon={<TrendingUp />} 
                    iconPosition="start"
                    sx={{ minHeight: 48 }}
                  />
                  <Tab 
                    label="详细分析" 
                    icon={<Analytics />} 
                    iconPosition="start"
                    sx={{ minHeight: 48 }}
                  />
                  <Tab 
                    label="技术图表" 
                    icon={<ShowChart />} 
                    iconPosition="start"
                    sx={{ minHeight: 48 }}
                  />
                </Tabs>
              </Paper>

              {/* 标签页内容 */}
              <Box sx={{ flex: 1, m: 2, mt: 0 }}>
                <TabPanel value={activeTab} index={0}>
                  <TradingSignals 
                    allSignals={allSignals}
                    comprehensiveAdvice={comprehensiveAdvice}
                    backtestResult={backtestResult}
                  />
                </TabPanel>
                
                <TabPanel value={activeTab} index={1}>
                  <DetailedAnalysis 
                    allSignals={allSignals}
                  />
                </TabPanel>
                
                <TabPanel value={activeTab} index={2}>
                  <TradingViewChart 
                    allStockData={allStockData}
                    stockInfo={stockInfo}
                  />
                </TabPanel>
              </Box>
            </Box>
          ) : (
            <Box sx={{ flex: 1, p: 2 }}>
              <Card sx={{ height: '100%' }}>
                <CardContent sx={{ 
                  height: '100%', 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  bgcolor: 'background.paper',
                  borderRadius: 0,
                  border: '2px dashed',
                  borderColor: 'rgba(255,255,255,0.1)'
                }}>
                  <Info sx={{ fontSize: 64, color: 'text.secondary', mb: 2, opacity: 0.6 }} />
                  <Typography variant="h6" color="text.primary" gutterBottom>
                    等待分析
                  </Typography>
                  <Typography variant="body2" color="text.secondary" textAlign="center">
                    请在左侧输入股票代码，<br />
                    然后点击"生成交易信号"按钮开始多周期分析
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          )}
        </Box>
      </Box>

      {/* 回到顶部按钮 */}
      <Zoom in={showScrollTop}>
        <Fab
          color="primary"
          size="small"
          onClick={scrollToTop}
          sx={{
            position: 'fixed',
            bottom: 16,
            right: 16,
          }}
        >
          <KeyboardArrowUp />
        </Fab>
      </Zoom>
    </Box>
  );
};

export default HomePage; 