import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Grid,
  Paper,
  Alert,
  Tabs,
  Tab,
  Collapse,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  Info,
  ExpandMore,
  ExpandLess,
  Timeline,
  Security,
  AccountBalance,
  TableRows,
} from '@mui/icons-material';

const TradingSignals = ({ allSignals, comprehensiveAdvice, backtestResult }) => {
  const [selectedPeriod, setSelectedPeriod] = useState('daily');
  const [expandedSections, setExpandedSections] = useState({
    overview: true,
    details: true,
    indicators: false,
    fundamentals: false,
    risk: false,
    trades: true,
  });

  if (!allSignals || !comprehensiveAdvice) return null;

  const handlePeriodChange = (event, newPeriod) => {
    if (newPeriod !== null) {
      setSelectedPeriod(newPeriod);
    }
  };

  // 切换区域展开状态
  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // 获取当前选中周期的信号
  const currentSignals = allSignals[selectedPeriod]?.signals;
  if (!currentSignals) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="info">
          当前周期暂无交易信号数据
        </Alert>
      </Box>
    );
  }

  // 确定信号类型样式
  const getSignalTypeColor = (signalType) => {
    if (signalType.includes('强烈买入')) return 'success';
    if (signalType.includes('买入')) return 'success';
    if (signalType.includes('强烈卖出')) return 'error';
    if (signalType.includes('卖出')) return 'secondary';
    return 'warning';
  };

  // 确定风险等级样式
  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel) {
      case '高': return 'error';
      case '中': return 'warning';
      default: return 'info';
    }
  };

  // 获取信号图标
  const getSignalIcon = (signalType) => {
    if (signalType.includes('买入')) return <CheckCircle />;
    if (signalType.includes('卖出')) return <Cancel />;
    return <Info />;
  };

  // 智能渲染对象
  const renderValue = (value) => {
    if (value === null || value === undefined) {
      return '暂无数据';
    }
    
    if (typeof value === 'object') {
      // 处理 latest_values 对象
      if (value.latest_values && typeof value.latest_values === 'object') {
        const entries = Object.entries(value.latest_values);
        if (entries.length === 0) return '暂无数据';
        
        return entries.map(([key, val]) => {
          const displayValue = typeof val === 'number' ? val.toFixed(2) : String(val);
          return `${key}: ${displayValue}`;
        }).join(', ');
      }
      
      // 处理 latest_value 对象
      if (value.latest_value !== undefined) {
        const displayValue = typeof value.latest_value === 'number' 
          ? value.latest_value.toFixed(2) 
          : String(value.latest_value);
        return displayValue;
      }
      
      // 处理其他对象
      try {
        const entries = Object.entries(value);
        if (entries.length === 0) return '暂无数据';
        
        return entries.map(([key, val]) => {
          const displayValue = typeof val === 'number' ? val.toFixed(2) : String(val);
          return `${key}: ${displayValue}`;
        }).join(', ');
      } catch (e) {
        return JSON.stringify(value);
      }
    }
    
    if (typeof value === 'number') {
      return value.toFixed(2);
    }
    
    return String(value);
  };

  const buildChip = (periodKey, periodName, sig, keySeed) => {
    let color = 'default';
    if (sig.includes('强烈买入')) color = 'success';
    else if (sig.includes('买入')) color = 'success';
    else if (sig.includes('强烈卖出')) color = 'error';
    else if (sig.includes('卖出')) color = 'secondary';
    else color = 'warning';
    return (
      <Chip
        key={`${periodKey}-${keySeed}`} 
        label={`${periodName} ${sig}`} 
        color={color} 
        size="small" 
        sx={{ mr: 0.5, mb: 0.5 }}
      />
    );
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ p: 0, flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* 综合建议区域 - 固定在顶部 */}
        <Box sx={{ p: 2, bgcolor: 'primary.50', borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h5" component="h2" sx={{ mb: 1, fontWeight: 'bold' }}>
            {comprehensiveAdvice.overall_signal}
          </Typography>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {comprehensiveAdvice.advice}
          </Typography>

          {/* 统计信息 - 紧凑布局 */}
          <Grid container spacing={1} sx={{ mb: 1 }}>
            <Grid item xs={3}>
              <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'success.main', color: 'white' }}>
                <Typography variant="h6">{comprehensiveAdvice.statistics.buy_count}</Typography>
                <Typography variant="caption">买入</Typography>
              </Paper>
            </Grid>
            <Grid item xs={3}>
              <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'error.main', color: 'white' }}>
                <Typography variant="h6">{comprehensiveAdvice.statistics.sell_count}</Typography>
                <Typography variant="caption">卖出</Typography>
              </Paper>
            </Grid>
            <Grid item xs={3}>
              <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'warning.main', color: 'white' }}>
                <Typography variant="h6">{comprehensiveAdvice.statistics.hold_count}</Typography>
                <Typography variant="caption">观望</Typography>
              </Paper>
            </Grid>
            <Grid item xs={3}>
              <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'info.main', color: 'white' }}>
                <Typography variant="h6">{comprehensiveAdvice.statistics.total_periods}</Typography>
                <Typography variant="caption">总周期</Typography>
              </Paper>
            </Grid>
          </Grid>

          {/* 回测结果 */}
          {backtestResult && (
            <Box sx={{ mt: 1 }}>
              <Paper sx={{ p: 1, textAlign: 'center' }}>
                <Typography variant="body2">
                  回测收益率: {backtestResult.total_return_pct}% | 收益金额: ¥{backtestResult.profit_amount.toLocaleString()} | 期末资产: ¥{backtestResult.capital_end.toLocaleString()}
                </Typography>
              </Paper>

              {/* 交易明细表格 - 可折叠 */}
              {backtestResult.details && (
                <Card variant="outlined" sx={{ mt: 1 }}>
                  <Box 
                    sx={{ 
                      p: 1.5, 
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      bgcolor: 'background.default'
                    }}
                    onClick={() => toggleSection('trades')}
                  >
                    <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <TableRows color="info" />
                      交易明细 ({backtestResult.details.daily?.trades?.length || 0})
                    </Typography>
                    <IconButton size="small">
                      {expandedSections.trades ? <ExpandLess /> : <ExpandMore />}
                    </IconButton>
                  </Box>

                  <Collapse in={expandedSections.trades}>
                    <TableContainer component={Paper} sx={{ maxHeight: 300 }}>
                      <Table size="small" stickyHeader>
                        <TableHead>
                          <TableRow>
                            <TableCell>类型</TableCell>
                            <TableCell>时间</TableCell>
                            <TableCell>价格</TableCell>
                            <TableCell>收益%</TableCell>
                            <TableCell>收益额</TableCell>
                            <TableCell>决策</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {backtestResult.details.daily?.trades?.map((trade, idx) => {
                            let decisionChips = [];
                            if (trade.decisions && trade.decisions.length > 0) {
                              decisionChips = trade.decisions.map((d, chipIdx) => {
                                const label = ['15', '30', '60'].includes(d.period) ? `${d.period}min` : (allSignals?.[d.period]?.period_name || d.period);
                                return buildChip(d.period, label, d.signal_type, chipIdx);
                              });
                            } else {
                              // fallback to current signals snapshot
                              decisionChips = Object.entries(allSignals || {}).map(([key, data]) => {
                                const label = ['15', '30', '60'].includes(key) ? `${key}min` : (data.period_name || key);
                                const sig = data.signals?.signal_type || '未知';
                                return buildChip(key, label, sig, idx);
                              });
                            }

                            return (
                              <TableRow key={idx}>
                                <TableCell>{trade.type === 'buy' ? '买入' : '卖出'}</TableCell>
                                <TableCell>{trade.date}</TableCell>
                                <TableCell>{trade.price.toFixed(2)}</TableCell>
                                {trade.type === 'sell' ? (
                                  <>
                                    <TableCell
                                      sx={{ color: trade.profit_pct >= 0 ? 'error.main' : 'success.main' }}
                                    >
                                      {trade.profit_pct >= 0 ? '+' : ''}{trade.profit_pct.toFixed(2)}%
                                    </TableCell>
                                    <TableCell
                                      sx={{ color: trade.profit_amount >= 0 ? 'error.main' : 'success.main' }}
                                    >
                                      {trade.profit_amount >= 0 ? '+' : ''}{trade.profit_amount.toFixed(2)}
                                    </TableCell>
                                  </>
                                ) : (
                                  <>
                                    <TableCell>-</TableCell>
                                    <TableCell>-</TableCell>
                                  </>
                                )}
                                <TableCell sx={{ whiteSpace: 'normal' }}>
                                  <Box sx={{ display: 'flex', flexWrap: 'wrap' }}>
                                    {decisionChips}
                                  </Box>
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Collapse>
                </Card>
              )}
            </Box>
          )}
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
            {Object.entries(allSignals).map(([periodKey, periodData]) => (
              <Tab 
                key={periodKey} 
                value={periodKey} 
                label={periodData.period_name}
                sx={{ minHeight: 40, py: 1 }}
              />
            ))}
          </Tabs>
        </Box>

        {/* 周期内容 - 可滚动区域 */}
        <Box sx={{ flex: 1, overflow: 'auto' }}>
          <Box sx={{ p: 2 }}>
            {/* 当前周期信号概览 */}
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {getSignalIcon(currentSignals.signal_type)}
                  <Typography variant="h6" component="h3">
                    {currentSignals.signal_type}
                  </Typography>
                </Box>
                <Chip
                  label={`信号强度: ${currentSignals.signal_strength}`}
                  color={getSignalTypeColor(currentSignals.signal_type)}
                  size="small"
                />
              </Box>
              
              {currentSignals.advice && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  {currentSignals.advice}
                </Alert>
              )}
            </Box>

            {/* 信号详情 - 可折叠区域 */}
            <Grid container spacing={2}>
              {/* 技术指标信号 */}
              <Grid item xs={12}>
                <Card variant="outlined">
                  <Box 
                    sx={{ 
                      p: 1.5, 
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      bgcolor: 'background.default'
                    }}
                    onClick={() => toggleSection('indicators')}
                  >
                    <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Timeline color="primary" />
                      技术指标信号
                    </Typography>
                    <IconButton size="small">
                      {expandedSections.indicators ? <ExpandLess /> : <ExpandMore />}
                    </IconButton>
                  </Box>
                  
                  <Collapse in={expandedSections.indicators}>
                    <Box sx={{ p: 1.5, pt: 0 }}>
                      <Grid container spacing={1}>
                        {currentSignals.indicators && Object.entries(currentSignals.indicators).map(([key, value]) => (
                          <Grid item xs={6} key={key}>
                            <Paper sx={{ p: 1, bgcolor: 'background.paper' }}>
                              <Typography variant="caption" color="text.secondary">
                                {key}
                              </Typography>
                              <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                                {renderValue(value)}
                              </Typography>
                            </Paper>
                          </Grid>
                        ))}
                      </Grid>
                    </Box>
                  </Collapse>
                </Card>
              </Grid>

              {/* 基本面分析 */}
              <Grid item xs={12}>
                <Card variant="outlined">
                  <Box 
                    sx={{ 
                      p: 1.5, 
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      bgcolor: 'background.default'
                    }}
                    onClick={() => toggleSection('fundamentals')}
                  >
                    <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <AccountBalance color="secondary" />
                      基本面分析
                    </Typography>
                    <IconButton size="small">
                      {expandedSections.fundamentals ? <ExpandLess /> : <ExpandMore />}
                    </IconButton>
                  </Box>
                  
                  <Collapse in={expandedSections.fundamentals}>
                    <Box sx={{ p: 1.5, pt: 0 }}>
                      {currentSignals.fundamental_analysis ? (
                        <Grid container spacing={1}>
                          {Object.entries(currentSignals.fundamental_analysis).map(([key, value]) => (
                            <Grid item xs={6} key={key}>
                              <Paper sx={{ p: 1, bgcolor: 'grey.50' }}>
                                <Typography variant="caption" color="text.secondary">
                                  {key}
                                </Typography>
                                <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                                  {renderValue(value)}
                                </Typography>
                              </Paper>
                            </Grid>
                          ))}
                        </Grid>
                      ) : (
                        <Alert severity="info" sx={{ fontSize: '0.875rem' }}>
                          暂无基本面数据
                        </Alert>
                      )}
                    </Box>
                  </Collapse>
                </Card>
              </Grid>

              {/* 风险评估 */}
              <Grid item xs={12}>
                <Card variant="outlined">
                  <Box 
                    sx={{ 
                      p: 1.5, 
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      bgcolor: 'background.default'
                    }}
                    onClick={() => toggleSection('risk')}
                  >
                    <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Security color="warning" />
                      风险评估
                    </Typography>
                    <IconButton size="small">
                      {expandedSections.risk ? <ExpandLess /> : <ExpandMore />}
                    </IconButton>
                  </Box>
                  
                  <Collapse in={expandedSections.risk}>
                    <Box sx={{ p: 1.5, pt: 0 }}>
                      {currentSignals.risk_assessment ? (
                        <Grid container spacing={1}>
                          <Grid item xs={6}>
                            <Paper sx={{ p: 1, bgcolor: 'grey.50' }}>
                              <Typography variant="caption" color="text.secondary">
                                风险等级
                              </Typography>
                              <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                                <Chip 
                                  label={currentSignals.risk_assessment.risk_level || '未知'}
                                  color={getRiskLevelColor(currentSignals.risk_assessment.risk_level)}
                                  size="small"
                                />
                              </Typography>
                            </Paper>
                          </Grid>
                          <Grid item xs={6}>
                            <Paper sx={{ p: 1, bgcolor: 'grey.50' }}>
                              <Typography variant="caption" color="text.secondary">
                                风险因子
                              </Typography>
                              <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                                {currentSignals.risk_assessment.risk_factors?.join(', ') || '无'}
                              </Typography>
                            </Paper>
                          </Grid>
                        </Grid>
                      ) : (
                        <Alert severity="info" sx={{ fontSize: '0.875rem' }}>
                          暂无风险评估数据
                        </Alert>
                      )}
                    </Box>
                  </Collapse>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default TradingSignals; 