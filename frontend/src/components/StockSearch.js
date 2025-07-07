import React, { useState, useEffect, useRef } from 'react';
import {
  TextField,
  Autocomplete,
  Box,
  Typography,
  Chip,
  Paper,
  IconButton,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import { 
  Search as SearchIcon,
  Delete as DeleteIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { stockAPI } from '../utils/api';

const StockSearch = ({ value, onChange, onSelect }) => {
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [showHistory, setShowHistory] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);
  const searchTimeoutRef = useRef(null);

  // 示例股票代码
  const exampleStocks = [
    { code: '000001', name: '平安银行', sector: '银行' },
    { code: '000002', name: '万科A', sector: '房地产' },
    { code: '600000', name: '浦发银行', sector: '银行' },
    { code: '600036', name: '招商银行', sector: '银行' },
    { code: '000858', name: '五粮液', sector: '白酒' },
  ];

  // 从localStorage加载搜索历史
  useEffect(() => {
    const savedHistory = localStorage.getItem('stockSearchHistory');
    if (savedHistory) {
      try {
        setSearchHistory(JSON.parse(savedHistory));
      } catch (error) {
        console.error('加载搜索历史失败:', error);
        setSearchHistory([]);
      }
    }
  }, []);

  // 保存搜索历史到localStorage
  const saveSearchHistory = (history) => {
    try {
      localStorage.setItem('stockSearchHistory', JSON.stringify(history));
    } catch (error) {
      console.error('保存搜索历史失败:', error);
    }
  };

  // 添加搜索历史
  const addToHistory = (stock) => {
    const newHistory = [
      stock,
      ...searchHistory.filter(item => item.code !== stock.code)
    ].slice(0, 10); // 最多保存10条记录
    
    setSearchHistory(newHistory);
    saveSearchHistory(newHistory);
  };

  // 删除搜索历史
  const removeFromHistory = (codeToRemove) => {
    const newHistory = searchHistory.filter(item => item.code !== codeToRemove);
    setSearchHistory(newHistory);
    saveSearchHistory(newHistory);
  };

  // 清空搜索历史
  const clearHistory = () => {
    setSearchHistory([]);
    localStorage.removeItem('stockSearchHistory');
  };

  // 搜索股票
  const searchStocks = async (query) => {
    if (!query.trim()) {
      setOptions([]);
      return;
    }

    setLoading(true);
    try {
      const response = await stockAPI.searchStocks(query, 8);
      if (response.success) {
        setOptions(response.stocks);
      } else {
        setOptions([]);
      }
    } catch (error) {
      console.error('搜索失败:', error);
      setOptions([]);
    } finally {
      setLoading(false);
    }
  };

  // 处理输入变化
  const handleInputChange = (event, newInputValue) => {
    setInputValue(newInputValue);
    setShowHistory(false);
    
    // 清除之前的定时器
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // 延迟搜索
    searchTimeoutRef.current = setTimeout(() => {
      searchStocks(newInputValue);
    }, 300);
  };

  // 处理选择
  const handleChange = (event, newValue) => {
    // 确保传递的是字符串
    let valueToSet = '';
    let selectedStock = null;
    
    if (typeof newValue === 'string') {
      valueToSet = newValue;
    } else if (newValue && typeof newValue === 'object' && newValue.code) {
      valueToSet = newValue.code;
      selectedStock = newValue;
    }
    
    onChange(valueToSet);
    if (valueToSet && onSelect) {
      onSelect(valueToSet);
    }
    
    // 添加到搜索历史
    if (selectedStock) {
      addToHistory(selectedStock);
    }
  };

  // 处理搜索框聚焦
  const handleFocus = () => {
    if (!inputValue.trim() && searchHistory.length > 0) {
      setShowHistory(true);
    }
  };

  // 处理搜索框失焦
  const handleBlur = () => {
    // 延迟隐藏历史记录，让用户有时间点击
    setTimeout(() => {
      setShowHistory(false);
    }, 200);
  };

  // 从历史记录中选择
  const selectFromHistory = (stock) => {
    setInputValue(stock.code);
    onChange(stock.code);
    if (onSelect) onSelect(stock.code);
    setShowHistory(false);
  };

  // 清理定时器
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  return (
    <Box sx={{ position: 'relative' }}>
      <Autocomplete
        value={value}
        onChange={handleChange}
        inputValue={inputValue}
        onInputChange={handleInputChange}
        options={options}
        loading={loading}
        freeSolo
        onFocus={handleFocus}
        onBlur={handleBlur}
        getOptionLabel={(option) => {
          if (typeof option === 'string') return option;
          if (option && typeof option === 'object' && option.code) {
            return option.name ? `${option.code} ${option.name}` : option.code;
          }
          return '';
        }}
        renderInput={(params) => (
          <TextField
            {...params}
            label="股票代码或公司名称"
            placeholder="请输入股票代码、公司名称或拼音，如：000001、平安银行、pab"
            variant="outlined"
            fullWidth
            InputProps={{
              ...params.InputProps,
              startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
            }}
          />
        )}
        renderOption={(props, option) => {
          const { key, ...otherProps } = props;
          return (
            <Box component="li" key={key} {...otherProps}>
              <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body1" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                    {option.code}
                  </Typography>
                  <Chip 
                    label={option.sector} 
                    size="small" 
                    variant="outlined"
                    sx={{ fontSize: '0.75rem' }}
                  />
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {option.name}
                </Typography>
              </Box>
            </Box>
          );
        }}
        noOptionsText="未找到匹配的股票"
        loadingText="搜索中..."
        filterOptions={(x) => x} // 禁用内置过滤
      />
      
      {/* 搜索历史记录 */}
      {showHistory && searchHistory.length > 0 && (
        <Paper 
          sx={{ 
            position: 'absolute', 
            top: '100%', 
            left: 0, 
            right: 0, 
            zIndex: 1000, 
            mt: 1, 
            maxHeight: 300, 
            overflow: 'auto',
            bgcolor: 'background.paper',
            border: 1,
            borderColor: 'divider',
            boxShadow: 3,
          }}
        >
          <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <HistoryIcon fontSize="small" />
              搜索历史
            </Typography>
            <Chip 
              label="清空" 
              size="small" 
              variant="outlined" 
              clickable
              onClick={clearHistory}
              sx={{ fontSize: '0.75rem' }}
            />
          </Box>
          {searchHistory.map((stock) => (
            <ListItem 
              key={stock.code} 
              button 
              onClick={() => selectFromHistory(stock)}
              sx={{ 
                py: 1,
                '&:hover': {
                  bgcolor: 'action.hover',
                }
              }}
            >
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                      {stock.code}
                    </Typography>
                    <Chip 
                      label={stock.sector} 
                      size="small" 
                      variant="outlined"
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                  </Box>
                }
                secondary={stock.name}
              />
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFromHistory(stock.code);
                  }}
                  sx={{ 
                    color: 'error.main',
                    '&:hover': {
                      bgcolor: 'error.light',
                      color: 'white',
                    }
                  }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </Paper>
      )}
      
      {/* 示例股票代码 */}
      <Paper sx={{ mt: 2, p: 2, bgcolor: 'primary.50' }}>
        <Typography variant="subtitle2" color="primary" gutterBottom>
          💡 常用股票代码示例：
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {exampleStocks.map((stock) => (
            <Chip
              key={stock.code}
              label={`${stock.code} ${stock.name}`}
              size="small"
              clickable
              onClick={() => {
                setInputValue(stock.code);
                onChange(stock.code);
                if (onSelect) onSelect(stock.code);
                // 添加到搜索历史
                addToHistory(stock);
              }}
              sx={{ 
                cursor: 'pointer',
                '&:hover': {
                  bgcolor: 'primary.light',
                  color: 'white',
                }
              }}
            />
          ))}
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          深市股票以000、002、300开头，沪市股票以600、601、603开头
        </Typography>
      </Paper>
    </Box>
  );
};

export default StockSearch; 